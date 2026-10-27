-- Glowing pads that take you somewhere: the VAYU lobby to its sky pool and back, and the
-- stunt park floor to the top of the mega ramp. Each pad names its partner in "Target".
local folder = workspace:WaitForChild("Portals")

for _, pad in ipairs(folder:GetChildren()) do
	local target = pad:FindFirstChild("Target")
	local label = pad:FindFirstChild("Label")
	if pad:IsA("BasePart") and target then
		local prompt = Instance.new("ProximityPrompt")
		prompt.ActionText = label and label.Value or "Go"
		prompt.ObjectText = "Portal"
		prompt.HoldDuration = 0.3
		prompt.MaxActivationDistance = 10
		prompt.RequiresLineOfSight = false
		prompt.Parent = pad
		local tag = Instance.new("BillboardGui")
		tag.Size = UDim2.fromOffset(220, 40)
		tag.StudsOffset = Vector3.new(0, 5, 0)
		tag.MaxDistance = 150
		tag.LightInfluence = 0
		local text = Instance.new("TextLabel")
		text.Size = UDim2.fromScale(1, 1)
		text.BackgroundTransparency = 1
		text.Font = Enum.Font.GothamBold
		text.TextScaled = true
		text.TextColor3 = Color3.fromRGB(225, 190, 255)
		text.TextStrokeTransparency = 0.4
		text.Text = prompt.ActionText
		text.Parent = tag
		tag.Parent = pad
		prompt.Triggered:Connect(function(player)
			local character = player.Character
			local humanoid = character and character:FindFirstChildOfClass("Humanoid")
			local dest = folder:FindFirstChild(target.Value)
			if humanoid and humanoid.Health > 0 and dest then
				humanoid.Sit = false
				character:PivotTo(CFrame.new(dest.Position + Vector3.new(0, 4, 0)))
			end
		end)
	end
end
