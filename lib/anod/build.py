from __future__ import annotations

from e3.anod.action import (
    Build,
    DownloadSource,
    GetSource,
    InstallSource,
    Checkout,
    CreateSource,
)
from e3 import hash
from e3.anod.checkout import CheckoutManager
from e3.env import Env
from e3.job.walk import Walk
from e3.job import Job, EmptyJob
from e3.net.http import HTTPSession
from e3.anod.status import ReturnValue
from e3.archive import unpack_archive
from e3.fingerprint import Fingerprint
from e3.fs import mkdir, sync_tree, rm, cp
from e3.os.fs import cd

import json
import logging
import os
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from e3.anod.spec import Anod
    from e3.collection.dag import DAG
    from e3.anod.sandbox import SandBox


def add_anod_files_to_fingerprint(
    anod_instance: Anod, fingerprint: Fingerprint
) -> None:
    """Add the Anod's spec and yaml files to the given fingerprint.

    :param anod_instance: an Anod instance.
    :type anod_instance: Anod
    :param fingerprint: The fingerprint to update.
    :type fingerprint: e3.fingerprint.Fingerprint.
    """
    anod_specs = [
        c.name
        for c in anod_instance.__class__.__mro__
        if c.__name__ != "Anod" and "Anod" in (sc.__name__ for sc in c.__mro__)
    ]
    for spec_name in anod_specs:
        fingerprint.add_file(os.path.join(anod_instance.spec_dir, spec_name + ".anod"))
    for yaml_name in anod_instance.data_files:
        fingerprint.add_file(os.path.join(anod_instance.spec_dir, yaml_name + ".yaml"))

    deps = getattr(anod_instance, "%s_deps" % anod_instance.kind, ())
    for dep in deps:
        if isinstance(dep, anod_instance.BuildVar):
            fingerprint.add(dep.name, dep.value)


class FSFBuildEmptyJob(EmptyJob):
    def __init__(self, uid, data, notify_end, sandbox):
        super(FSFBuildEmptyJob, self).__init__(uid, data, notify_end)


class FSFBuildJob(Job):
    def __init__(self, uid, data, notify_end, sandbox):
        super(FSFBuildJob, self).__init__(uid, data, notify_end)
        self.run_status = ReturnValue.unknown
        self.sandbox = sandbox

    @property
    def status(self):
        return self.run_status

    def run(self):
        print(self.data)


class FSFBuildBuildJob(FSFBuildJob):
    def run(self):
        try:
            rm(self.data.anod_instance.build_space.build_dir, recursive=True)
            mkdir(self.data.anod_instance.build_space.build_dir)
            rm(self.data.anod_instance.build_space.install_dir, recursive=True)
            mkdir(self.data.anod_instance.build_space.install_dir)
            Env().store()
            cd(self.data.anod_instance.build_space.build_dir)
            self.data.anod_instance.jobs = Env().build.cpu.cores
            self.data.anod_instance.build()
            Env().restore()
            self.run_status = ReturnValue.success
        except Exception:
            logging.exception("got exception while building")
            self.run_status = ReturnValue.failure


class FSFBuildInstallSource(FSFBuildJob):
    def run(self):
        spec = self.data.spec
        source = self.data.source
        spec.build_space.create(quiet=True)
        filename = os.path.join(self.sandbox.tmp_cache_dir, self.data.source.name)

        source.set_other_sources(getattr(spec, "%s_source_list" % spec.kind, []))
        dest = os.path.join(spec.build_space.src_dir, source.dest)
        if os.path.isdir(filename):
            sync_tree(
                filename, dest, ignore=source.ignore, delete=True
            )
        else:
            mkdir(os.path.join(spec.build_space.src_dir, source.dest))
            unpack_archive(
                filename=os.path.join(
                    self.sandbox.tmp_cache_dir, self.data.source.name
                ),
                dest=os.path.join(spec.build_space.src_dir, source.dest),
                remove_root_dir=source.remove_root_dir,
                unpack_cmd=source.unpack_cmd,
                ignore=source.ignore,
                delete=True,
            )
        self.run_status = ReturnValue.success


class FSFBuildDownloadSource(FSFBuildJob):
    def run(self):
        builder = self.data.builder
        cache_dir = self.sandbox.tmp_cache_dir

        skip = False
        if os.path.isfile(os.path.join(cache_dir, builder.filename)) and os.path.isfile(
            os.path.join(cache_dir, builder.filename + ".sha1")
        ):
            with open(os.path.join(cache_dir, builder.filename + ".sha1"), "rb") as f:
                checksum = f.read(1024).decode()
            skip = checksum == hash.sha1(os.path.join(cache_dir, builder.filename))

        if skip:
            self.run_status = ReturnValue.skip
        else:
            if builder.url.startswith("https://") or builder.url.startswith("http://"):

                if os.path.isfile(os.path.join(cache_dir, builder.filename)):
                    rm(os.path.join(cache_dir, builder.filename))
                if os.path.isfile(os.path.join(cache_dir, builder.filename + ".sha1")):
                    rm(os.path.join(cache_dir, builder.filename + ".sha1"))

                tries = 0
                delay = 5
                max_tries = 5
                result = None
                while tries < max_tries:
                    tries += 1
                    try:
                        s = HTTPSession(base_urls=[builder.base_url])
                        result = s.download_file(
                            url=builder.filename, dest=cache_dir, filename=builder.name
                        )
                    except BaseException:
                        result = None
    
                    if result is None:
                        if tries < max_tries:
                            logging.warning(f"failed to download sources, retrying in {delay} seconds...")
                        else:
                            logging.error(f"failed to download sources (retried {max_tries} times)")
                        rm(os.path.join(cache_dir, builder.filename))
                        self.run_status = ReturnValue.failure
                    else:
                        self.run_status = ReturnValue.success
                        with open(
                            os.path.join(cache_dir, builder.filename + ".sha1"), "w"
                        ) as f:
                            f.write(hash.sha1(os.path.join(cache_dir, builder.filename)))
                        break

                    time.sleep(delay if tries < max_tries else 0)
                    delay *= 2
            else:
                cp(
                    os.path.join(self.sandbox.specs_dir, "patches", builder.url),
                    cache_dir,
                )
                self.run_status = ReturnValue.success


class FSFBuildCheckout(FSFBuildJob):
    def run(self):
        manager = CheckoutManager(
            name=self.data.repo_name, working_dir=self.sandbox.vcs_dir
        )
        repo_data = self.data.repo_data
        result = manager.update(
            vcs=repo_data["vcs"],
            url=repo_data["url"],
            revision=repo_data.get("revision"),
        )
        self.run_status = result


class RepositoryState(object):
    """Wrapper around metadata to be compatible with specs API 1.4."""

    def __init__(self, metadata):
        self.rev = metadata.get("new-rev")
        self.url = metadata.get("url")
        self.branch = metadata.get("revision")


class FSFBuildCreateSource(FSFBuildJob):
    def run(self):
        source_name = self.data.source_name
        anod_instance = self.data.anod_instance
        builder = next(
            (b for b in anod_instance.source_pkg_build if b.name == source_name), None
        )
        source_dest = os.path.join(self.sandbox.tmp_cache_dir, source_name)
        repository_states = {}
        for repo_name in builder.checkout:
            repository_states[repo_name] = {
                "working_dir": os.path.join(self.sandbox.vcs_dir, repo_name)
            }
        builder.prepare_src(repository_states, source_dest)
        self.run_status = ReturnValue.success


class FSFBuildBuilder(Walk):

    JOB_CLASSES = {
        Build: FSFBuildBuildJob,
        DownloadSource: FSFBuildDownloadSource,
        GetSource: FSFBuildEmptyJob,
        InstallSource: FSFBuildInstallSource,
        Checkout: FSFBuildCheckout,
        CreateSource: FSFBuildCreateSource,
    }

    def __init__(self, actions: DAG, sandbox: SandBox, force: bool):
        self.sandbox = sandbox
        self.force = force
        mkdir(self.fingerprints_dir)
        super(FSFBuildBuilder, self).__init__(actions)

    def compute_fingerprint(self, uid, data, is_prediction=False):
        """See Walk.compute_fingerprint."""
        if is_prediction and self.force:
            # Force a rebuild
            return None

        # All fingerprints start with the same minimum amount
        # of data: The fingerprint of all the predecessors.
        f = Fingerprint()
        for pred_uid in self.actions.get_predecessors(uid):
            if self.new_fingerprints[pred_uid] is None:
                logging.debug(
                    "Returning no fingerprint for %s"
                    " (predecessor %s has no fingerprint)",
                    uid,
                    pred_uid,
                )
                return None
            else:
                f.add(pred_uid, self.new_fingerprints[pred_uid].checksum())
        if isinstance(data, Checkout):
            if is_prediction:
                # We cannot predict the fingerprint of a checkout without
                # performing it, thus checkout will always be executed.
                return None

            m = CheckoutManager(name=data.repo_name, working_dir=self.sandbox.vcs_dir)
            with open(m.metadata_file) as fd:
                content = json.load(fd)
            f.add(data.repo_name + ".url", content["url"])
            f.add(data.repo_name + ".commit", content["new_commit"])
        elif isinstance(data, (CreateSource, Build)):
            add_anod_files_to_fingerprint(data.anod_instance, f)
        elif isinstance(data, InstallSource):
            add_anod_files_to_fingerprint(data.spec, f)
        return f

    def save_fingerprint(self, uid, fingerprint):
        """See Walk.save_fingerprint."""
        filename = self.fingerprint_filename(uid)
        if fingerprint is None:
            rm(filename)
        else:
            fingerprint.save_to_file(filename)

    @property
    def fingerprints_dir(self):
        """Return the directory where fingerprints are stored.

        :rtype: str
        """
        return os.path.join(self.sandbox.root_dir, "fingerprints")

    def fingerprint_filename(self, uid):
        """Return the full path to the fingerprint of the given job.

        :param uid: A unique Job ID.
        :type uid: str
        :rtype: str
        """
        return os.path.join(self.fingerprints_dir, uid + ".json")

    def load_previous_fingerprint(self, uid):
        """See Walk.load_previous_fingerprint."""
        return Fingerprint.load_from_file(self.fingerprint_filename(uid))

    def should_execute_action(self, uid, previous_fingerprint, new_fingerprint):
        """See Walk.should_execute_action."""
        # The function is override only to provide some additional logging
        # information.
        result = super(FSFBuildBuilder, self).should_execute_action(
            uid, previous_fingerprint, new_fingerprint
        )
        if result:
            if previous_fingerprint is None:
                logging.debug("%s has no previous fingerprint", uid)
            elif new_fingerprint is None:
                logging.debug("%s always is always executed", uid)
            else:
                data = previous_fingerprint.compare_to(new_fingerprint)
                data_str = []
                for el in data.get("updated"):
                    data_str.append("(M)%s" % el)
                for el in data.get("new"):
                    data_str.append("(+)%s" % el)
                for el in data.get("obsolete"):
                    data_str.append("(-)%s" % el)
                logging.info("%s triggered by:\n    %s", uid, "\n    ".join(data_str))
        return result

    def create_job(self, uid, data, predecessors, notify_end):
        return self.JOB_CLASSES.get(data.__class__, FSFBuildJob)(
            uid, data, notify_end, sandbox=self.sandbox
        )
