local dir = app.params["dir"]
local n = tonumber(app.params["n"])
local first = Image{ fromFile = dir.."/o000.png" }
local spr = Sprite(first.width, first.height, ColorMode.RGB)
spr.cels[1].image = first
for i=1,n-1 do
  local img = Image{ fromFile = string.format("%s/o%03d.png", dir, i) }
  local fr = spr:newEmptyFrame()
  spr:newCel(spr.layers[1], fr, img, Point(0,0))
end
for _,f in ipairs(spr.frames) do f.duration = 0.075 end
spr:saveCopyAs(dir.."/demoness.aseprite")
spr:saveCopyAs(dir.."/demoness.gif")
print("frames", #spr.frames)
