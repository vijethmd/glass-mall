-- Speedometer and driving hints while you sit in a car's driver seat.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local player = Players.LocalPlayer
local KMH = 0.2857 * 3.6 -- studs/s -> km/h at 3.5 studs per metre

local gui = Instance.new("ScreenGui")
gui.Name = "CarHUD"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")

local panel = Instance.new("Frame")
panel.AnchorPoint = Vector2.new(1, 1)
panel.Size = UDim2.new(0, 210, 0, 92)
panel.Position = UDim2.new(1, -18, 1, -18)
panel.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
panel.BackgroundTransparency = 0.15
panel.Visible = false
panel.Parent = gui
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 12)
corner.Parent = panel

local speed = Instance.new("TextLabel")
speed.Size = UDim2.new(1, -24, 0, 50)
speed.Position = UDim2.new(0, 12, 0, 6)
speed.BackgroundTransparency = 1
speed.Font = Enum.Font.GothamBlack
speed.TextSize = 40
speed.TextXAlignment = Enum.TextXAlignment.Left
speed.TextColor3 = Color3.fromRGB(120, 225, 245)
speed.Parent = panel

local unit = Instance.new("TextLabel")
unit.Size = UDim2.new(0, 60, 0, 50)
unit.Position = UDim2.new(1, -72, 0, 6)
unit.BackgroundTransparency = 1
unit.Font = Enum.Font.GothamMedium
unit.TextSize = 16
unit.TextXAlignment = Enum.TextXAlignment.Right
unit.TextColor3 = Color3.fromRGB(200, 210, 214)
unit.Text = "km/h"
unit.Parent = panel

local hint = Instance.new("TextLabel")
hint.Size = UDim2.new(1, -24, 0, 30)
hint.Position = UDim2.new(0, 12, 0, 56)
hint.BackgroundTransparency = 1
hint.Font = Enum.Font.Gotham
hint.TextSize = 13
hint.TextXAlignment = Enum.TextXAlignment.Left
hint.TextColor3 = Color3.fromRGB(200, 210, 214)
hint.Text = "W/S drive  ·  A/D steer  ·  Space get out"
hint.Parent = panel

RunService.RenderStepped:Connect(function()
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local seat = humanoid and humanoid.SeatPart
	if seat and seat:IsA("VehicleSeat") then
		panel.Visible = true
		speed.Text = tostring(math.floor(seat.AssemblyLinearVelocity.Magnitude * KMH + 0.5))
	else
		panel.Visible = false
	end
end)
