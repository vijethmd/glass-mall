-- Counters that hand you something: coffee in the cafés, dosa and noodles in the food court,
-- popcorn at the cinema, ice cream on the beach, balloons in the toy shop. Every part with a
-- Vendor StringValue gets a prompt; the item is a Tool built from a few parts. Click to
-- eat or drink it; after a few bites it's gone. It's all free.
local Players = game:GetService("Players")
local Debris = game:GetService("Debris")

local MAX_CARRIED = 4
local SOUND = {
	bought = "rbxassetid://9113728042",
	sip = "rbxassetid://9119956310",
	gulp = "rbxassetid://9114171957",
}

local function rgb(r, g, b)
	return Color3.fromRGB(r, g, b)
end

-- each item: what it's made of. Offsets are from the handle, in studs.
local function cup(body, lid, extra)
	return function(add)
		add("Handle", Vector3.new(0.55, 0.8, 0.55), body, Enum.Material.SmoothPlastic, CFrame.new())
		add("Lid", Vector3.new(0.6, 0.08, 0.6), lid, Enum.Material.SmoothPlastic, CFrame.new(0, 0.44, 0))
		add("Sleeve", Vector3.new(0.58, 0.3, 0.58), rgb(150, 104, 66), Enum.Material.Fabric, CFrame.new(0, -0.05, 0))
		if extra then
			extra(add)
		end
	end
end
local function glass(liquid)
	return function(add)
		add("Handle", Vector3.new(0.5, 0.8, 0.5), rgb(220, 240, 250), Enum.Material.Glass, CFrame.new(), 0.5)
		add("Drink", Vector3.new(0.42, 0.6, 0.42), liquid, Enum.Material.SmoothPlastic, CFrame.new(0, -0.08, 0))
		add("Straw", Vector3.new(0.07, 0.9, 0.07), rgb(240, 80, 90), Enum.Material.SmoothPlastic,
			CFrame.new(0.1, 0.45, 0) * CFrame.Angles(0, 0, math.rad(-12)))
	end
end
local function cone(scoop, second)
	return function(add)
		add("Handle", Vector3.new(0.34, 0.7, 0.34), rgb(214, 160, 90), Enum.Material.WoodPlanks, CFrame.new())
		add("Scoop", Vector3.new(0.56, 0.56, 0.56), scoop, Enum.Material.SmoothPlastic, CFrame.new(0, 0.48, 0), 0, "Ball")
		if second then
			add("Scoop", Vector3.new(0.48, 0.48, 0.48), second, Enum.Material.SmoothPlastic, CFrame.new(0, 0.86, 0), 0, "Ball")
		end
	end
end

local ITEMS = {
	Coffee = { cup(rgb(250, 250, 248), rgb(40, 40, 44)), "sip" },
	["Filter coffee"] = { cup(rgb(200, 200, 196), rgb(150, 104, 66)), "sip" },
	["Bubble tea"] = {
		function(add)
			glass(rgb(214, 170, 130))(add)
			for k = 1, 5 do
				add("Pearl", Vector3.new(0.1, 0.1, 0.1), rgb(30, 20, 16), Enum.Material.SmoothPlastic,
					CFrame.new(math.cos(k) * 0.12, -0.3, math.sin(k) * 0.12), 0, "Ball")
			end
		end,
		"sip",
	},
	Mocktail = { glass(rgb(250, 120, 80)), "sip" },
	["Fresh juice"] = { glass(rgb(250, 170, 40)), "sip" },
	Slushie = { glass(rgb(60, 160, 250)), "sip" },
	Soda = { glass(rgb(120, 60, 30)), "gulp" },
	["Coconut water"] = {
		function(add)
			add("Handle", Vector3.new(0.8, 0.8, 0.8), rgb(110, 160, 60), Enum.Material.Wood, CFrame.new(), 0, "Ball")
			add("Straw", Vector3.new(0.07, 0.8, 0.07), rgb(240, 240, 236), Enum.Material.SmoothPlastic,
				CFrame.new(0.05, 0.55, 0) * CFrame.Angles(0, 0, math.rad(-15)))
		end,
		"gulp",
	},
	["Ice cream"] = { cone(rgb(250, 200, 90), rgb(250, 170, 190)), "sip" },
	Gelato = { cone(rgb(150, 210, 130)), "sip" },
	["Ice lolly"] = {
		function(add)
			add("Handle", Vector3.new(0.08, 0.5, 0.08), rgb(214, 180, 120), Enum.Material.Wood, CFrame.new())
			add("Lolly", Vector3.new(0.4, 0.7, 0.18), rgb(250, 80, 120), Enum.Material.SmoothPlastic, CFrame.new(0, 0.55, 0))
		end,
		"sip",
	},
	["Pizza slice"] = {
		function(add)
			add("Handle", Vector3.new(0.12, 0.9, 0.7), rgb(240, 190, 90), Enum.Material.SmoothPlastic, CFrame.new(), 0,
				"Wedge")
			for k = 1, 3 do
				add("Topping", Vector3.new(0.14, 0.14, 0.14), rgb(200, 40, 30), Enum.Material.SmoothPlastic,
					CFrame.new(0.07, -0.25 + k * 0.15, 0.1 - k * 0.04), 0, "Ball")
			end
		end,
		"sip",
	},
	["Masala dosa"] = {
		function(add)
			add("Handle", Vector3.new(1.2, 0.08, 1.0), rgb(250, 250, 248), Enum.Material.SmoothPlastic, CFrame.new())
			add("Dosa", Vector3.new(1.4, 0.35, 0.35), rgb(214, 150, 60), Enum.Material.SmoothPlastic, CFrame.new(0, 0.2, 0),
				0, "Cylinder")
			add("Chutney", Vector3.new(0.3, 0.12, 0.3), rgb(240, 240, 230), Enum.Material.SmoothPlastic,
				CFrame.new(0.4, 0.1, 0.4), 0, "Ball")
		end,
		"sip",
	},
	Noodles = {
		function(add)
			add("Handle", Vector3.new(0.6, 0.7, 0.6), rgb(250, 250, 248), Enum.Material.SmoothPlastic, CFrame.new())
			add("Noodles", Vector3.new(0.5, 0.15, 0.5), rgb(240, 200, 110), Enum.Material.Fabric, CFrame.new(0, 0.38, 0))
			for k = -1, 1, 2 do
				add("Chopstick", Vector3.new(0.05, 1.0, 0.05), rgb(150, 104, 66), Enum.Material.Wood,
					CFrame.new(k * 0.06, 0.6, 0) * CFrame.Angles(0, 0, math.rad(10 * k)))
			end
		end,
		"sip",
	},
	Popcorn = {
		function(add)
			add("Handle", Vector3.new(0.6, 0.8, 0.5), rgb(220, 40, 40), Enum.Material.SmoothPlastic, CFrame.new())
			add("Stripe", Vector3.new(0.62, 0.8, 0.12), rgb(250, 250, 248), Enum.Material.SmoothPlastic, CFrame.new())
			for k = 1, 7 do
				add("Popcorn", Vector3.new(0.2, 0.2, 0.2), rgb(250, 236, 180), Enum.Material.Fabric,
					CFrame.new(math.cos(k * 2) * 0.18, 0.45 + (k % 3) * 0.06, math.sin(k * 2) * 0.14), 0, "Ball")
			end
		end,
		"sip",
	},
	Snack = {
		function(add)
			add("Handle", Vector3.new(0.6, 0.8, 0.2), rgb(240, 190, 60), Enum.Material.Foil, CFrame.new())
		end,
		"sip",
	},
	["Candy floss"] = {
		function(add)
			add("Handle", Vector3.new(0.07, 0.8, 0.07), rgb(240, 240, 236), Enum.Material.SmoothPlastic, CFrame.new())
			add("Floss", Vector3.new(0.9, 0.9, 0.9), rgb(250, 160, 200), Enum.Material.Fabric, CFrame.new(0, 0.75, 0), 0,
				"Ball")
		end,
		"sip",
	},
	Book = {
		function(add)
			add("Handle", Vector3.new(0.2, 0.9, 0.65), rgb(60, 110, 170), Enum.Material.SmoothPlastic, CFrame.new())
			add("Pages", Vector3.new(0.16, 0.86, 0.6), rgb(250, 248, 240), Enum.Material.SmoothPlastic, CFrame.new(0, 0, 0.03))
		end,
		nil,
	},
	Bouquet = {
		function(add)
			add("Handle", Vector3.new(0.3, 0.9, 0.3), rgb(240, 236, 220), Enum.Material.Fabric, CFrame.new())
			for k = 1, 5 do
				add("Flower", Vector3.new(0.3, 0.3, 0.3), ({ rgb(230, 70, 90), rgb(250, 200, 60), rgb(240, 240, 236),
					rgb(200, 90, 200) })[k % 4 + 1], Enum.Material.Fabric,
					CFrame.new(math.cos(k * 1.3) * 0.15, 0.55 + (k % 2) * 0.1, math.sin(k * 1.3) * 0.15), 0, "Ball")
			end
		end,
		nil,
	},
	Balloon = {
		function(add)
			add("Handle", Vector3.new(0.15, 0.3, 0.15), rgb(240, 240, 236), Enum.Material.SmoothPlastic, CFrame.new())
			add("String", Vector3.new(0.03, 3.2, 0.03), rgb(240, 240, 236), Enum.Material.SmoothPlastic, CFrame.new(0, 1.7, 0))
			add("Balloon", Vector3.new(1.3, 1.6, 1.3), ({ rgb(230, 60, 70), rgb(60, 140, 240), rgb(250, 200, 40),
				rgb(80, 200, 120) })[math.random(4)], Enum.Material.SmoothPlastic, CFrame.new(0, 3.9, 0), 0, "Ball")
		end,
		nil,
	},
}

local function build(name)
	local spec = ITEMS[name]
	if not spec then
		return nil
	end
	local tool = Instance.new("Tool")
	tool.Name = name
	tool.CanBeDropped = false
	tool.RequiresHandle = true
	tool.ToolTip = spec[2] and "Click to enjoy" or name
	local handle
	spec[1](function(partName, size, color, material, offset, transparency, shape)
		local p = Instance.new("Part")
		p.Name = partName
		p.Size = size
		p.Color = color
		p.Material = material
		p.Transparency = transparency or 0
		p.CanCollide = false
		p.Massless = true
		p.TopSurface = Enum.SurfaceType.Smooth
		p.BottomSurface = Enum.SurfaceType.Smooth
		if shape == "Ball" then
			p.Shape = Enum.PartType.Ball
		elseif shape == "Cylinder" then
			p.Shape = Enum.PartType.Cylinder
		end
		if shape == "Wedge" then
			p:Destroy()
			p = Instance.new("WedgePart")
			p.Name = partName
			p.Size = size
			p.Color = color
			p.Material = material
			p.CanCollide = false
			p.Massless = true
		end
		if partName == "Handle" then
			handle = p
			p.CFrame = CFrame.new()
		else
			p.CFrame = offset -- the handle is built at the origin
			local w = Instance.new("WeldConstraint")
			w.Part0 = handle
			w.Part1 = p
			w.Parent = p
		end
		p.Parent = tool
	end)
	if not handle then
		tool:Destroy()
		return nil
	end
	tool.Grip = CFrame.new(0, -0.15, 0)
	local bites = 0
	tool.Activated:Connect(function()
		if not spec[2] then
			return
		end
		bites += 1
		local s = Instance.new("Sound")
		s.SoundId = SOUND[spec[2]] or SOUND.sip
		s.Volume = 0.6
		s.Parent = handle
		s:Play()
		Debris:AddItem(s, 3)
		local character = tool.Parent
		local head = character and character:FindFirstChild("Head")
		if head then
			local b = Instance.new("BillboardGui")
			b.Size = UDim2.fromOffset(90, 34)
			b.StudsOffset = Vector3.new(0, 2.2, 0)
			b.LightInfluence = 0
			local t = Instance.new("TextLabel")
			t.Size = UDim2.fromScale(1, 1)
			t.BackgroundTransparency = 1
			t.Font = Enum.Font.GothamBlack
			t.TextScaled = true
			t.TextColor3 = Color3.fromRGB(255, 220, 120)
			t.TextStrokeTransparency = 0.3
			t.Text = bites >= 3 and "Finished!" or "Yum!"
			t.Parent = b
			b.Parent = head
			Debris:AddItem(b, 1.4)
		end
		for _, p in ipairs(tool:GetChildren()) do
			if p:IsA("BasePart") and p ~= handle and p.Name ~= "String" and p.Name ~= "Balloon" then
				p.Size = p.Size * 0.85
			end
		end
		if bites >= 3 then
			task.delay(0.6, function()
				tool:Destroy()
			end)
		end
	end)
	return tool
end

local function give(player, name, at)
	local backpack = player:FindFirstChildOfClass("Backpack")
	local character = player.Character
	if not backpack or not character then
		return
	end
	local carried = {}
	for _, t in ipairs(backpack:GetChildren()) do
		if t:IsA("Tool") and ITEMS[t.Name] then
			table.insert(carried, t)
		end
	end
	for _, t in ipairs(character:GetChildren()) do
		if t:IsA("Tool") and ITEMS[t.Name] then
			table.insert(carried, t)
		end
	end
	while #carried >= MAX_CARRIED do
		table.remove(carried, 1):Destroy()
	end
	local tool = build(name)
	if not tool then
		return
	end
	tool.Parent = backpack
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid:EquipTool(tool)
	end
	local s = Instance.new("Sound")
	s.SoundId = SOUND.bought
	s.Volume = 0.5
	s.RollOffMaxDistance = 40
	s.Parent = at
	s:Play()
	Debris:AddItem(s, 3)
end

local function hook(part)
	local item = part:FindFirstChild("Vendor")
	if not part:IsA("BasePart") or not item or part:FindFirstChild("VendorPrompt") then
		return
	end
	local name = item.Value
	if not ITEMS[name] then
		warn("Vendors: no item called " .. name)
		return
	end
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "VendorPrompt"
	prompt.ActionText = "Get " .. string.lower(name)
	prompt.ObjectText = "Free"
	prompt.HoldDuration = 0.3
	prompt.MaxActivationDistance = 9
	prompt.RequiresLineOfSight = false
	prompt.Parent = part
	local last = {}
	prompt.Triggered:Connect(function(player)
		if last[player] and os.clock() - last[player] < 1.5 then
			return
		end
		last[player] = os.clock()
		give(player, name, part)
	end)
end

for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("StringValue") and d.Name == "Vendor" and d.Parent then
		hook(d.Parent)
	end
end
