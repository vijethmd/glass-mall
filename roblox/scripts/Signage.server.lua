-- Builds every sign in the place from the values stored on its part:
--   SignText (StringValue)  what it says
--   Face     (StringValue)  which face of the part it is drawn on (default Back)
--   Style    (StringValue)  fascia | led | screen | directory | button
--   Accent   (Color3Value)  second colour for animated signs
-- Gradients named "Anim" are animated on each player's screen by ClientFX.
local function gradient(frame, c0, c1)
	local g = Instance.new("UIGradient")
	g.Name = "Anim"
	g.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, c0),
		ColorSequenceKeypoint.new(0.5, c1),
		ColorSequenceKeypoint.new(1, c0),
	})
	g.Parent = frame
end

local function build(part)
	local text = part:FindFirstChild("SignText")
	local face = part:FindFirstChild("Face")
	local style = part:FindFirstChild("Style")
	local accent = part:FindFirstChild("Accent")
	local kind = style and style.Value or "fascia"

	local gui = Instance.new("SurfaceGui")
	gui.Name = "Sign"
	gui.Face = Enum.NormalId[face and face.Value or "Back"]
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = kind == "button" and 80 or 30
	gui.LightInfluence = 0
	gui.Brightness = kind == "screen" and 2 or 1.5

	local bg = Instance.new("Frame")
	bg.Size = UDim2.fromScale(1, 1)
	bg.BorderSizePixel = 0
	bg.BackgroundTransparency = 1
	bg.Parent = gui

	if kind == "led" or kind == "screen" then
		bg.BackgroundTransparency = 0
		bg.BackgroundColor3 = Color3.new(1, 1, 1)
		local base = kind == "led" and Color3.fromRGB(16, 30, 120) or Color3.fromRGB(26, 18, 54)
		gradient(bg, base, accent and accent.Value or Color3.fromRGB(210, 50, 170))
	elseif kind == "directory" then
		bg.BackgroundTransparency = 0.05
		bg.BackgroundColor3 = Color3.fromRGB(18, 22, 26)
	elseif kind == "button" then
		bg.BackgroundTransparency = 0
		bg.BackgroundColor3 = Color3.fromRGB(30, 34, 40)
	end

	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.TextScaled = true
	label.Font = kind == "directory" and Enum.Font.Gotham or Enum.Font.GothamBold
	label.TextColor3 = Color3.new(1, 1, 1)
	label.Text = text.Value
	if kind == "directory" then
		label.Size = UDim2.fromScale(0.86, 0.86)
		label.Position = UDim2.fromScale(0.07, 0.07)
		label.TextXAlignment = Enum.TextXAlignment.Left
		label.TextYAlignment = Enum.TextYAlignment.Top
	elseif kind == "screen" then
		label.Size = UDim2.fromScale(0.8, 0.5)
		label.Position = UDim2.fromScale(0.1, 0.25)
	else
		label.Size = UDim2.fromScale(0.9, 0.72)
		label.Position = UDim2.fromScale(0.05, 0.14)
	end
	label.Parent = bg
	gui.Parent = part
end

for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("BasePart") and d:FindFirstChild("SignText") then
		build(d)
	end
end
