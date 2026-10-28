-- Your explorer passport: notices which place you are in (CityData.find), asks the server for
-- a stamp the first time, and shows a card when you get one. The Passport button (or P)
-- opens the book: every place in the city, the ones you have found ticked off.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local CityData = require(ReplicatedStorage:WaitForChild("CityData"))
local remote = ReplicatedStorage:WaitForChild("Passport")
local player = Players.LocalPlayer
local ACCENT = Color3.fromRGB(120, 225, 245)

local book, total, asked = {}, #CityData.KEYS, {}

local gui = Instance.new("ScreenGui")
gui.Name = "Passport"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")

local function corner(p, r)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r)
	c.Parent = p
end

local function label(parent, text, size, font, color, x, y, w, h, align)
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1
	t.Position = UDim2.new(0, x, 0, y)
	t.Size = UDim2.new(w <= 1 and w or 0, w > 1 and w or 0, 0, h)
	t.Font = font
	t.TextSize = size
	t.TextColor3 = color
	t.TextXAlignment = align or Enum.TextXAlignment.Left
	t.TextTruncate = Enum.TextTruncate.AtEnd
	t.Text = text
	t.Parent = parent
	return t
end

-- ------------------------------------------------------------------ the button
local button = Instance.new("TextButton")
button.AnchorPoint = Vector2.new(0, 0.5)
button.Size = UDim2.new(0, 120, 0, 42)
button.Position = UDim2.new(0, 16, 0.5, 100)
button.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
button.BackgroundTransparency = 0.1
button.Font = Enum.Font.GothamBold
button.TextSize = 15
button.TextColor3 = ACCENT
button.Parent = gui
corner(button, 21)

local function count()
	local n = 0
	for _ in pairs(book) do
		n += 1
	end
	return n
end
local function refreshButton()
	button.Text = string.format("Passport %d/%d", count(), total)
end
refreshButton()

-- ------------------------------------------------------------------ the stamp card
local card = Instance.new("Frame")
card.AnchorPoint = Vector2.new(0.5, 0)
card.Size = UDim2.new(0, 380, 0, 96)
card.Position = UDim2.new(0.5, 0, 0, -220)
card.Visible = false
card.BackgroundColor3 = Color3.fromRGB(16, 22, 28)
card.BackgroundTransparency = 0.05
card.Parent = gui
corner(card, 14)
local stroke = Instance.new("UIStroke", card)
stroke.Color = Color3.fromRGB(255, 200, 80)
stroke.Thickness = 2
local stamp = label(card, "★", 44, Enum.Font.GothamBlack, Color3.fromRGB(255, 200, 80), 14, 18, 56, 56,
	Enum.TextXAlignment.Center)
local kicker = label(card, "NEW PLACE DISCOVERED", 12, Enum.Font.GothamBold, Color3.fromRGB(255, 200, 80), 80, 12, 280, 16)
local nameL = label(card, "", 20, Enum.Font.GothamBlack, Color3.new(1, 1, 1), 80, 30, 285, 26)
local whereL = label(card, "", 14, Enum.Font.Gotham, Color3.fromRGB(190, 205, 212), 80, 56, 285, 18)
local prizeL = label(card, "", 13, Enum.Font.GothamMedium, ACCENT, 80, 74, 285, 16)
local chime = Instance.new("Sound")
chime.SoundId = "rbxassetid://9116395089"
chime.Volume = 0.6
chime.Parent = gui

local queue, showing = {}, false
local function showNext()
	if showing or #queue == 0 then
		return
	end
	showing = true
	local s = table.remove(queue, 1)
	nameL.Text, whereL.Text, prizeL.Text = s[1], s[2], s[3]
	chime:Play()
	stamp.Rotation = -30
	TweenService:Create(stamp, TweenInfo.new(0.5, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
	TweenService:Create(card, TweenInfo.new(0.45, Enum.EasingStyle.Back), { Position = UDim2.new(0.5, 0, 0, 62) }):Play()
	card.Visible = true
	task.delay(3.4, function()
		TweenService:Create(card, TweenInfo.new(0.4), { Position = UDim2.new(0.5, 0, 0, -220) }):Play()
		task.wait(0.5)
		card.Visible = false
		showing = false
		showNext()
	end)
end

-- ------------------------------------------------------------------ the book
local panel = Instance.new("Frame")
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.Position = UDim2.fromScale(0.5, 0.5)
panel.Size = UDim2.new(0, 460, 0.78, 0)
panel.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
panel.BackgroundTransparency = 0.04
panel.Visible = false
panel.Parent = gui
corner(panel, 16)
local maxSize = Instance.new("UISizeConstraint", panel)
maxSize.MaxSize = Vector2.new(460, 640)
label(panel, "EXPLORER PASSPORT", 22, Enum.Font.GothamBlack, ACCENT, 20, 14, 330, 28)
local progress = label(panel, "", 14, Enum.Font.Gotham, Color3.fromRGB(200, 214, 220), 20, 44, 400, 18)
local close = Instance.new("TextButton")
close.Size = UDim2.fromOffset(36, 36)
close.Position = UDim2.new(1, -50, 0, 14)
close.BackgroundColor3 = Color3.fromRGB(32, 42, 48)
close.Text = "✕"
close.Font = Enum.Font.GothamBold
close.TextSize = 18
close.TextColor3 = Color3.new(1, 1, 1)
close.Parent = panel
corner(close, 18)
local bar = Instance.new("Frame")
bar.Position = UDim2.new(0, 20, 0, 70)
bar.Size = UDim2.new(1, -40, 0, 8)
bar.BackgroundColor3 = Color3.fromRGB(32, 42, 48)
bar.Parent = panel
corner(bar, 4)
local fill = Instance.new("Frame")
fill.Size = UDim2.fromScale(0, 1)
fill.BackgroundColor3 = Color3.fromRGB(255, 200, 80)
fill.Parent = bar
corner(fill, 4)
local list = Instance.new("ScrollingFrame")
list.Position = UDim2.new(0, 12, 0, 90)
list.Size = UDim2.new(1, -24, 1, -102)
list.BackgroundTransparency = 1
list.BorderSizePixel = 0
list.ScrollBarThickness = 6
list.AutomaticCanvasSize = Enum.AutomaticSize.Y
list.CanvasSize = UDim2.new()
list.Parent = panel
local layout = Instance.new("UIListLayout", list)
layout.SortOrder = Enum.SortOrder.LayoutOrder
layout.Padding = UDim.new(0, 2)

-- the book's chapters: the part of "where" before the first " · "
local chapters, order = {}, {}
do
	local seen = {}
	for i, d in ipairs(CityData.DISCOVERIES) do
		local key = CityData.KEY_OF[i]
		if not seen[key] then
			seen[key] = true
			local chapter = string.split(d[2], " · ")[1]
			if not chapters[chapter] then
				chapters[chapter] = {}
				table.insert(order, chapter)
			end
			table.insert(chapters[chapter], { key = key, name = d[1], where = d[2] })
		end
	end
	table.sort(order)
end

local function rebuild()
	for _, c in ipairs(list:GetChildren()) do
		if not c:IsA("UIListLayout") then
			c:Destroy()
		end
	end
	local n = 0
	for ci, chapter in ipairs(order) do
		local entries = chapters[chapter]
		local got = 0
		for _, e in ipairs(entries) do
			if book[e.key] then
				got += 1
			end
		end
		n += 1
		local h = label(list, string.format("%s   %d/%d", string.upper(chapter), got, #entries), 13, Enum.Font.GothamBold,
			got == #entries and Color3.fromRGB(255, 200, 80) or ACCENT, 0, 0, 1, 26)
		h.LayoutOrder = n
		for _, e in ipairs(entries) do
			n += 1
			local found = book[e.key]
			local row = label(list, found and ("✓  " .. e.name .. "   ·   " .. e.where) or ("·  ???   ·   " .. e.where), 13,
				found and Enum.Font.GothamMedium or Enum.Font.Gotham,
				found and Color3.new(1, 1, 1) or Color3.fromRGB(110, 124, 130), 8, 0, 1, 20)
			row.LayoutOrder = n
		end
		if ci > 400 then
			break
		end
	end
	local c = count()
	progress.Text = string.format("%d of %d places found  ·  3 coins for every new one", c, total)
	fill.Size = UDim2.fromScale(total > 0 and c / total or 0, 1)
end

local function toggle()
	panel.Visible = not panel.Visible
	if panel.Visible then
		rebuild()
	end
end
button.Activated:Connect(toggle)
close.Activated:Connect(toggle)
UserInputService.InputBegan:Connect(function(input, processed)
	if not processed and input.KeyCode == Enum.KeyCode.P then
		toggle()
	end
end)

-- ------------------------------------------------------------------ talking to the server
remote.OnClientEvent:Connect(function(kind, a, b, c, d, e, f)
	if kind == "book" then
		book = {}
		for _, key in ipairs(a) do
			book[key] = true
		end
		total = b or total
		refreshButton()
	elseif kind == "stamp" then
		book[a] = true
		total = e or total
		refreshButton()
		table.insert(queue, { b, c, string.format("+%d coins  ·  %d of %d found", f or 0, d, total) })
		showNext()
		if panel.Visible then
			rebuild()
		end
	end
end)
remote:FireServer("sync")

-- a place counts once you have stood in it for a moment: riding a lift past a floor doesn't
local here, since = nil, 0
while true do
	task.wait(0.4)
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if root then
		local index, _, key = CityData.find(root.Position)
		if key ~= here then
			here, since = key, os.clock()
		end
		local still = math.abs(root.AssemblyLinearVelocity.Y) < 4
		if index and still and os.clock() - since > 1.5 and not book[key]
			and (not asked[key] or os.clock() - asked[key] > 4) then
			asked[key] = os.clock()
			remote:FireServer("visit", index)
		end
	end
end
