#!/bin/bash

set -e

CRATES="gnat_native gnat_arm_elf gnat_riscv64_elf gnat_avr_elf gprbuild gnatcov gnatprove"

COUNT=0

for crate in ${CRATES}; do
    echo ${crate}
    VERSIONS=$(alr search ${crate} --full  | grep ${crate}| awk '{ print $2}')
    for version in ${VERSIONS}; do
        set -e
        alr get ${crate}=${version}
        COUNT=$((${COUNT} + 1))
    done
done

if [ "${COUNT}" -eq "0" ]; then
    echo "No crate downloaded..."
    exit 1
fi
