-- Сборка laplace-oracle.aseprite из покадровых слоёв.
-- Запуск:  aseprite -b --script-param root=<папка final> --script export-aseprite.lua
-- В <папка final> должны лежать layers/<имя слоя>/f000.png ... (в репозиторий не входят: берутся из сборки pipeline/oracle-v3/build.py).
local ROOT=app.params["root"]
assert(ROOT, "укажи --script-param root=<папка final>")
local s=Sprite(480,270,ColorMode.RGB)
local durations={0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1}
for i=1,110 do if i>1 then s:newEmptyFrame() end; s.frames[i].duration=durations[i] end
local layer=s.layers[1]
layer.name="Environment"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Environment/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,110}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={53,54,55,56,57,58,59,60,61,62,63,64,107}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={105,109}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={106,108}
app.command.LinkCels()
local layer=s:newLayer()
layer.name="Table"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Table/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,110}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={105,109}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={106,108}
app.command.LinkCels()
local layer=s:newLayer()
layer.name="Books"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Books/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,110}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={105,109}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={106,108}
app.command.LinkCels()
local layer=s:newLayer()
layer.name="Orb light"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Orb light/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={14,93}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={16,29,81,91,102}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={17,30,80,101}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={18,31,79,103}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={19,89}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={22,35,75,97}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={23,36,49,74,86}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={24,85}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={28,41,69}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={32,78}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={33,77}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={34,76}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={37,48,50,73}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={38,72}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={39,71}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={40,70}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={42,43,67,68}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={44,66,82}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={45,65}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={46,52,94}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={47,51,98}
app.command.LinkCels()
local layer=s:newLayer()
layer.name="Orb"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Orb/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={1,2,3,4,5,6,7,8,9,10,11,12,13,110}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={53,54,55,56,57,58,59,60,61,62,63,64}
app.command.LinkCels()
local layer=s:newLayer()
layer.name="Pages behind"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Pages behind/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
local layer=s:newLayer()
layer.name="Demoness"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Demoness/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={1,110}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={13,14,15,16,17,18,19,20,21,22,23,24}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={28,47}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={32,33,42,43,52}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={53,54,55}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={56,57,58}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={59,60,61,62,63,64}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={65,74,81,91,92,102}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={69,70}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={71,88}
app.command.LinkCels()
app.activeLayer=layer
app.range.layers={layer}
app.range.frames={77,95}
app.command.LinkCels()
local layer=s:newLayer()
layer.name="Pages in front"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Pages in front/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
local layer=s:newLayer()
layer.name="Sparks"
for i=1,110 do
 local im=Image{fromFile=string.format(ROOT.."/layers/Sparks/f%03d.png",i-1)}
 if not im:isEmpty() then s:newCel(layer,i,im,Point(0,0)) end
end
local t=s:newTag(1,12);t.name="01-entrance"
local t=s:newTag(13,24);t.name="02-touch-and-birth"
local t=s:newTag(25,52);t.name="03-paper-semicircle"
local t=s:newTag(53,64);t.name="04-look"
local t=s:newTag(65,80);t.name="05-gather-three"
local t=s:newTag(81,104);t.name="06-three-page-answer"
local t=s:newTag(105,110);t.name="07-reset"
s:saveAs(ROOT.."/laplace-oracle.aseprite")
print("saved "..#s.frames.." frames, "..#s.layers.." layers")