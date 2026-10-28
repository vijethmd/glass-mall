-- The loading screen: Glass City's name over a slow sunset while the city streams in, with
-- tips about what there is to do. It fades out once you are standing in the city.
local Players = game:GetService("Players")
local ReplicatedFirst = game:GetService("ReplicatedFirst")
local TweenService = game:GetService("TweenService")
local ContentProvider = game:GetService("ContentProvider")

local player = Players.LocalPlayer
local TIPS = {
	"Every building has an inside. Walk in, call the lift with E and pick any floor.",
	"Your passport stamps every new place you find: 3 coins each.",
	"Press M for the map. Click a gold pin to travel there.",
	"Hold E on a glowing pad to get a car. Drive with W A S D.",
	"Fireworks light up Glass Bay every night.",
	"Play the arcade machines on the mall's 3F to win coins.",
	"The Glass Spire's skywalk has a glass floor, 200 metres up.",
	"Free coffee, dosa, gelato and popcorn: press E at any counter.",
	"When the monsoon comes, the city gets very wet. Find a roof!",
}

pcall(function()
	ReplicatedFirst:RemoveDefaultLoadingScreen()
end)

local gui = Instance.new("ScreenGui")
gui.Name = "Loading"
gui.IgnoreGuiInset = true
gui.DisplayOrder = 100
gui.ResetOnSpawn = false
local bg = Instance.new("Frame")
bg.Size = UDim2.fromScale(1, 1)
bg.BackgroundColor3 = Color3.new(1, 1, 1)
bg.Parent = gui
local grad = Instance.new("UIGradient", bg)
grad.Rotation = 90
grad.Color = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(14, 20, 48)),
	ColorSequenceKeypoint.new(0.55, Color3.fromRGB(180, 80, 110)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 170, 90)),
})

-- a skyline of glass along the bottom
math.randomseed(7)
local x = 0
while x < 1 do
	local w = 0.025 + math.random() * 0.05
	local h = 0.12 + math.random() * 0.33
	local b = Instance.new("Frame")
	b.AnchorPoint = Vector2.new(0, 1)
	b.Position = UDim2.fromScale(x, 1)
	b.Size = UDim2.fromScale(w, h)
	b.BackgroundColor3 = Color3.fromRGB(20, 24, 44)
	b.BorderSizePixel = 0
	b.Parent = bg
	for k = 1, math.random(3, 9) do
		local win = Instance.new("Frame")
		win.Position = UDim2.fromScale(0.15 + math.random() * 0.6, math.random() * 0.9)
		win.Size = UDim2.fromScale(0.14, 0.02)
		win.BackgroundColor3 = Color3.fromRGB(255, 214, 140)
		win.BackgroundTransparency = math.random() < 0.4 and 0 or 0.6
		win.BorderSizePixel = 0
		win.Parent = b
	end
	x += w + 0.003
end

local title = Instance.new("TextLabel")
title.AnchorPoint = Vector2.new(0.5, 0.5)
title.Position = UDim2.fromScale(0.5, 0.34)
title.Size = UDim2.fromScale(0.8, 0.14)
title.BackgroundTransparency = 1
title.Font = Enum.Font.GothamBlack
title.TextScaled = true
title.TextColor3 = Color3.new(1, 1, 1)
title.Text = "GLASS CITY"
title.Parent = bg
local cap = Instance.new("UITextSizeConstraint", title)
cap.MaxTextSize = 96
local sub = Instance.new("TextLabel")
sub.AnchorPoint = Vector2.new(0.5, 0.5)
sub.Position = UDim2.fromScale(0.5, 0.44)
sub.Size = UDim2.fromScale(0.8, 0.05)
sub.BackgroundTransparency = 1
sub.Font = Enum.Font.GothamMedium
sub.TextScaled = true
sub.TextColor3 = Color3.fromRGB(230, 236, 240)
sub.Text = "A five-storey glass mall and the whole city around it"
sub.Parent = bg
Instance.new("UITextSizeConstraint", sub).MaxTextSize = 26
local tip = sub:Clone()
tip.Position = UDim2.fromScale(0.5, 0.56)
tip.Font = Enum.Font.Gotham
tip.TextColor3 = Color3.fromRGB(255, 236, 200)
tip.Text = TIPS[1]
tip.Parent = bg
local status = sub:Clone()
status.Position = UDim2.fromScale(0.5, 0.63)
status.Size = UDim2.fromScale(0.6, 0.035)
status.TextColor3 = Color3.fromRGB(200, 210, 220)
status.Text = "Building the city"
status.Parent = bg
gui.Parent = player:WaitForChild("PlayerGui")

local started = os.clock()
local done = false
task.spawn(function()
	local i = 1
	while not done do
		task.wait(3.2)
		i = i % #TIPS + 1
		tip.Text = TIPS[i]
	end
end)
task.spawn(function()
	local dots = 0
	while not done do
		dots = dots % 3 + 1
		local q = ContentProvider.RequestQueueSize
		status.Text = "Building the city" .. string.rep(".", dots) .. (q > 0 and ("   " .. q .. " to go") or "")
		task.wait(0.4)
	end
end)

if not game:IsLoaded() then
	game.Loaded:Wait()
end
local character = player.Character or player.CharacterAdded:Wait()
character:WaitForChild("HumanoidRootPart", 20)
while os.clock() - started < 3.5 do
	task.wait(0.1)
end
done = true
for _, d in ipairs(bg:GetDescendants()) do
	if d:IsA("TextLabel") then
		TweenService:Create(d, TweenInfo.new(0.8), { TextTransparency = 1 }):Play()
	elseif d:IsA("Frame") then
		TweenService:Create(d, TweenInfo.new(0.8), { BackgroundTransparency = 1 }):Play()
	end
end
TweenService:Create(bg, TweenInfo.new(1), { BackgroundTransparency = 1 }):Play()
task.wait(1.1)
gui:Destroy()
