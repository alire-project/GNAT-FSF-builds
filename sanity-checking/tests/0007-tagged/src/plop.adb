with Ada.Text_IO;

package body Plop is
   procedure Print (This : A'Class) is
   begin
      Ada.Text_IO.Put_Line (This.Img);
   end Print;
end Plop;
