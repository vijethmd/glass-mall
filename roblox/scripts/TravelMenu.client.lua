-- The Travel button: jump to any district of Glass City.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer
local event = ReplicatedStorage:WaitForChild("Travel")
local NAMES = __PLACE_NAMES__

local gui = Instance.new("ScreenGui")
gui.Name = "TravelMenu"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")

local function corner(parent, r)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r)
	c.Parent = parent
end

local button = Instance.new("TextButton")
button.AnchorPoint = Vector2.new(0, 0.5)
button.Size = UDim2.new(0, 120, 0, 42)
button.Position = UDim2.new(0, 16, 0.5, 0)
button.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
button.BackgroundTransparency = 0.1
button.Font = Enum.Font.GothamBold
button.TextSize = 17
button.TextColor3 = Color3.fromRGB(120, 225, 245)
button.Text = "Travel"
button.Parent = gui
corner(button, 21)

local list = Instance.new("ScrollingFrame") -- scrolls when the screen is too short for every place
list.AnchorPoint = Vector2.new(0, 0.5)
list.Size = UDim2.new(0, 240, 0.8, 0)
list.Position = UDim2.new(0, 146, 0.5, 0)
list.CanvasSize = UDim2.new(0, 0, 0, 46 * #NAMES + 16)
list.ScrollBarThickness = 6
list.BorderSizePixel = 0
local fit = Instance.new("UISizeConstraint")
fit.MaxSize = Vector2.new(240, 46 * #NAMES + 16)
fit.Parent = list
list.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
list.BackgroundTransparency = 0.1
list.Visible = false
list.Parent = gui
corner(list, 14)
local layout = Instance.new("UIListLayout")
layout.Padding = UDim.new(0, 6)
layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
layout.SortOrder = Enum.SortOrder.LayoutOrder
layout.Parent = list
local pad = Instance.new("UIPadding")
pad.PaddingTop = UDim.new(0, 8)
pad.Parent = list

for i, name in ipairs(NAMES) do
	local b = Instance.new("TextButton")
	b.LayoutOrder = i
	b.Size = UDim2.new(1, -20, 0, 40)
	b.BackgroundColor3 = Color3.fromRGB(32, 42, 48)
	b.Font = Enum.Font.GothamMedium
	b.TextSize = 15
	b.TextColor3 = Color3.new(1, 1, 1)
	b.Text = name
	b.Parent = list
	corner(b, 10)
	b.Activated:Connect(function()
		list.Visible = false
		event:FireServer(name)
	end)
end

button.Activated:Connect(function()
	list.Visible = not list.Visible
end)
