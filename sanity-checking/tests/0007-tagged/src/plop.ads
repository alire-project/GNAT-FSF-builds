package Plop is
   type A is interface;

   function Img (This : A) return String is abstract;

   type B is new A with null record;
   function Img (This : B) return String is ("B");

   type C is new A with null record;
   function Img (This : C) return String is ("C");

   procedure Print (This : A'Class);
end Plop;
