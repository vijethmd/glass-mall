-- The people who work and live in Glass City: baristas, receptionists, the DJ and dancers in
-- the sky club, lifeguards, shop assistants, residents at home. Each stands at a marker in
-- workspace.Staff (StringValues Role and Anim). A character is only made while a player is
-- near, so the city can hold hundreds of them. Press E by anyone to say hello.
local Players = game:GetService("Players")

local NEAR, FAR = 150, 230 -- studs: make a character inside NEAR of a player, remove it past FAR
local PER_TICK = 5 -- characters made per pass, so a crowd appears over a second or two
local folder = workspace:WaitForChild("Staff")
local crowd = Instance.new("Folder")
crowd.Name = "People"
crowd.Parent = workspace

local ANIM = {
	idle = "rbxassetid://507766388",
	wave = "rbxassetid://507770239",
	cheer = "rbxassetid://507770677",
	dance = "rbxassetid://507771019",
	dance2 = "rbxassetid://507776043",
	dance3 = "rbxassetid://507777268",
	dj = "rbxassetid://507776720",
	sit = "rbxassetid://2506281703",
	laugh = "rbxassetid://507770818",
}
local ONE_SHOT = { wave = true, cheer = true, laugh = true }

local SKIN = {
	Color3.fromRGB(255, 220, 190), Color3.fromRGB(234, 184, 146), Color3.fromRGB(198, 140, 100),
	Color3.fromRGB(160, 105, 72), Color3.fromRGB(120, 78, 52), Color3.fromRGB(86, 58, 40),
}
local HAIR = { "62234425", "63690008", "451220849", "376524487", "62724852", "20573078", "" }
local CASUAL = {
	Color3.fromRGB(230, 90, 70), Color3.fromRGB(60, 120, 200), Color3.fromRGB(245, 245, 240),
	Color3.fromRGB(40, 44, 52), Color3.fromRGB(240, 190, 60), Color3.fromRGB(90, 170, 120),
	Color3.fromRGB(200, 120, 200), Color3.fromRGB(120, 200, 230),
}
local function rgb(r, g, b)
	return Color3.fromRGB(r, g, b)
end
-- what each job wears: top, trousers, and a cap for some
local UNIFORM = {
	Barista = { rgb(110, 70, 40), rgb(40, 40, 44) },
	Cook = { rgb(245, 245, 242), rgb(40, 40, 44) },
	Waiter = { rgb(20, 20, 24), rgb(20, 20, 24) },
	Bartender = { rgb(20, 20, 24), rgb(40, 40, 44) },
	Receptionist = { rgb(40, 60, 110), rgb(30, 34, 44) },
	Concierge = { rgb(90, 20, 40), rgb(30, 30, 34) },
	["Security guard"] = { rgb(24, 30, 50), rgb(24, 30, 50), "4819740796" },
	Lifeguard = { rgb(220, 40, 40), rgb(230, 200, 60), "48474313" },
	Doctor = { rgb(245, 245, 242), rgb(60, 120, 160) },
	["Spa therapist"] = { rgb(240, 236, 228), rgb(240, 236, 228) },
	["Bank teller"] = { rgb(40, 60, 110), rgb(40, 40, 44) },
	["Personal trainer"] = { rgb(240, 60, 80), rgb(30, 30, 34) },
	["Yoga teacher"] = { rgb(150, 210, 190), rgb(60, 60, 70) },
	DJ = { rgb(20, 20, 24), rgb(20, 20, 24), "48474313" },
	Housekeeper = { rgb(120, 150, 190), rgb(120, 150, 190) },
	["Cinema usher"] = { rgb(160, 30, 40), rgb(20, 20, 24) },
	Cashier = { rgb(60, 200, 230), rgb(40, 40, 44) },
}
local LINES = {
	Barista = { "One filter kaapi, coming up!", "The cardamom latte is very good today.", "Mind the cup, it's hot!" },
	Cook = { "Fresh off the tawa!", "Extra chutney? Of course.", "Best dosa in Glass City, I promise." },
	Waiter = { "A table by the window?", "The chef's special is the biryani.", "Enjoy your meal!" },
	Bartender = { "Mocktail? I'll make you something with mint.", "Best view in the city from up here." },
	Receptionist = { "The lifts are right behind me. Press E to call one.", "Every floor is open today. Have a look round!" },
	Concierge = { "Welcome home! The penthouse is at the top.", "Parcel for you? No? Have a lovely day." },
	["Security guard"] = { "Welcome to Glass Mall. Cinemas are on 4F.", "No running on the escalators, please!" },
	Lifeguard = { "Swim between the flags!", "Sea's lovely today. Watch the waves at the pier." },
	Doctor = { "Drink water and walk a lot. Glass City is perfect for that.", "You look healthy to me!" },
	DJ = { "This one's for Glass City!", "Hands up on the dance floor!" },
	Dancer = { "Come and dance!", "Best club in the city!", "Woo!" },
	Fan = { "Did you see that jump?!", "Try the mega ramp! Hold E on the pad for a car." },
	Resident = { "Oh! Hello, neighbour.", "Lovely view from up here, isn't it?", "Mind the shoes by the door." },
	["Cinema usher"] = { "Both films are showing now. Grab some popcorn!", "Screen 1 is on your left." },
	["Information desk"] = { "Shops on every floor, food court on 2F, arcade on 3F.", "The roof terrace is lovely at sunset." },
	["Ice cream seller"] = { "Mango is the favourite today!", "Two scoops? Go on." },
	["Car dealer"] = { "Fancy a test drive? There's a car pad outside.", "She does 0 to 100 in no time." },
	["Arcade attendant"] = { "Press E at a glowing screen to play. You win coins!" },
	Teacher = { "Today we're building a city out of glass!", "Who can count the floors of the Glass Spire?" },
	Trader = { "COIN is up 9.9%! Buy, buy, buy!", "The market never sleeps." },
}
local GENERIC = {
	"Lovely day in Glass City!",
	"Have you been up the Glass Spire? The skywalk has a glass floor!",
	"There's a gold coin hidden on most floors. Keep looking!",
	"Every building has an inside. Open the map with M and go exploring.",
	"The sky club on top of the towers is the best party in town.",
	"Watch the fireworks over the bay at night.",
	"Your passport stamps every new place you find.",
}

local rng = Random.new()
local templates = {} -- uniform key -> a character to clone
local markers = {}

local function pick(list)
	return list[rng:NextInteger(1, #list)]
end

local function look(role)
	local u = UNIFORM[role]
	if u then
		return role, u[1], u[2], u[3]
	end
	return "casual" .. rng:NextInteger(1, 6), pick(CASUAL), pick(CASUAL), nil
end

local function makeTemplate(key, top, bottom, hat)
	if templates[key] then
		return templates[key]
	end
	local desc = Instance.new("HumanoidDescription")
	desc.TorsoColor = top
	desc.LeftArmColor = top
	desc.RightArmColor = top
	desc.LeftLegColor = bottom
	desc.RightLegColor = bottom
	desc.HeadColor = SKIN[2]
	desc.HairAccessory = pick(HAIR)
	if hat then
		desc.HatAccessory = hat
	end
	local ok, model = pcall(function()
		return Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15)
	end)
	if not ok or not model then
		desc.HairAccessory = ""
		desc.HatAccessory = ""
		ok, model = pcall(function()
			return Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15)
		end)
	end
	if not ok or not model then
		return nil
	end
	local humanoid = model:FindFirstChildOfClass("Humanoid")
	humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	humanoid.BreakJointsOnDeath = false
	humanoid.RequiresNeck = false
	for _, state in ipairs({ Enum.HumanoidStateType.FallingDown, Enum.HumanoidStateType.Ragdoll,
		Enum.HumanoidStateType.Climbing, Enum.HumanoidStateType.Swimming, Enum.HumanoidStateType.Dead,
		Enum.HumanoidStateType.Jumping, Enum.HumanoidStateType.Freefall }) do
		humanoid:SetStateEnabled(state, false)
	end
	model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
	templates[key] = model
	return model
end

local SKIN_PARTS = { "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand" }

local function bubble(head, text)
	local old = head:FindFirstChild("Bubble")
	if old then
		old:Destroy()
	end
	local b = Instance.new("BillboardGui")
	b.Name = "Bubble"
	b.Size = UDim2.fromOffset(260, 64)
	b.StudsOffset = Vector3.new(0, 2.6, 0)
	b.MaxDistance = 60
	b.LightInfluence = 0
	local f = Instance.new("TextLabel")
	f.Size = UDim2.fromScale(1, 1)
	f.BackgroundColor3 = Color3.fromRGB(250, 250, 248)
	f.BackgroundTransparency = 0.05
	f.TextColor3 = Color3.fromRGB(20, 24, 28)
	f.Font = Enum.Font.GothamMedium
	f.TextSize = 16
	f.TextWrapped = true
	f.Text = text
	f.Parent = b
	Instance.new("UICorner", f).CornerRadius = UDim.new(0, 14)
	local pad = Instance.new("UIPadding", f)
	pad.PaddingLeft = UDim.new(0, 10)
	pad.PaddingRight = UDim.new(0, 10)
	b.Parent = head
	task.delay(5, function()
		if b.Parent then
			b:Destroy()
		end
	end)
end

local function play(animator, kind)
	local a = Instance.new("Animation")
	a.AnimationId = ANIM[kind] or ANIM.idle
	local ok, track = pcall(function()
		return animator:LoadAnimation(a)
	end)
	if ok and track then
		track.Looped = not ONE_SHOT[kind]
		track:Play(0.3)
		return track
	end
	return nil
end

local function nearestSeat(pos)
	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { crowd }
	local best, bestD = nil, 5
	for _, p in ipairs(workspace:GetPartBoundsInRadius(pos, 5, params)) do
		if p:IsA("Seat") and not p.Occupant and not p.Disabled then
			local d = (p.Position - pos).Magnitude
			if d < bestD then
				best, bestD = p, d
			end
		end
	end
	return best
end

local function spawnAt(mk)
	local role, top, bottom, hat = mk.role, nil, nil, nil
	local key
	key, top, bottom, hat = look(role)
	local template = makeTemplate(key, top, bottom, hat)
	if not template or not mk.part.Parent then
		return
	end
	local model = template:Clone()
	model.Name = role
	local skin = pick(SKIN)
	for _, n in ipairs(SKIN_PARTS) do
		local p = model:FindFirstChild(n)
		if p then
			p.Color = skin
		end
	end
	local humanoid = model:FindFirstChildOfClass("Humanoid")
	local root = model:FindFirstChild("HumanoidRootPart")
	if not humanoid or not root then
		model:Destroy()
		return
	end
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			d.CanCollide = false
			d.CanTouch = false
		end
	end
	local base = mk.part.CFrame
	local feet = mk.part.Position.Y - mk.part.Size.Y / 2
	local up = humanoid.HipHeight + root.Size.Y / 2
	root.Anchored = mk.anim ~= "sit"
	model:PivotTo(CFrame.new(base.Position.X, feet + up, base.Position.Z) * base.Rotation)
	model.Parent = crowd
	pcall(function()
		root:SetNetworkOwner(nil)
	end)
	local animator = humanoid:FindFirstChildOfClass("Animator") or Instance.new("Animator", humanoid)
	if mk.anim == "sit" then
		local seat = nearestSeat(base.Position)
		if seat then
			seat:Sit(humanoid)
		else
			root.Anchored = true
			play(animator, "idle")
		end
	else
		play(animator, ONE_SHOT[mk.anim] and "idle" or mk.anim)
		if ONE_SHOT[mk.anim] then
			task.spawn(function()
				while model.Parent do
					task.wait(rng:NextNumber(5, 11))
					if model.Parent then
						play(animator, mk.anim)
					end
				end
			end)
		end
	end

	local head = model:FindFirstChild("Head")
	if head then
		local tag = Instance.new("BillboardGui")
		tag.Name = "Role"
		tag.Size = UDim2.fromOffset(160, 22)
		tag.StudsOffset = Vector3.new(0, 1.5, 0)
		tag.MaxDistance = 28
		tag.LightInfluence = 0
		local t = Instance.new("TextLabel")
		t.Size = UDim2.fromScale(1, 1)
		t.BackgroundTransparency = 1
		t.Font = Enum.Font.GothamMedium
		t.TextSize = 14
		t.TextColor3 = Color3.fromRGB(235, 240, 242)
		t.TextStrokeTransparency = 0.5
		t.Text = role
		t.Parent = tag
		tag.Parent = head

		local prompt = Instance.new("ProximityPrompt")
		prompt.ActionText = "Say hello"
		prompt.ObjectText = role
		prompt.HoldDuration = 0
		prompt.MaxActivationDistance = 8
		prompt.RequiresLineOfSight = false
		prompt.Parent = root
		local lines = LINES[role]
		prompt.Triggered:Connect(function()
			local text = (lines and #lines > 0 and rng:NextNumber() < 0.7) and pick(lines) or pick(GENERIC)
			bubble(head, text)
			if mk.anim ~= "sit" then
				play(animator, "wave")
			end
		end)
	end
	mk.npc = model
end

for _, part in ipairs(folder:GetChildren()) do
	local role, anim = part:FindFirstChild("Role"), part:FindFirstChild("Anim")
	if part:IsA("BasePart") and role then
		table.insert(markers, { part = part, role = role.Value, anim = anim and anim.Value or "idle" })
	end
end

while true do
	local spots = {}
	for _, player in ipairs(Players:GetPlayers()) do
		local r = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if r then
			table.insert(spots, r.Position)
		end
	end
	local made = 0
	for _, mk in ipairs(markers) do
		local d = math.huge
		local p = mk.part.Position
		for _, s in ipairs(spots) do
			d = math.min(d, (s - p).Magnitude)
		end
		if mk.npc and (d > FAR or not mk.npc.Parent) then
			if mk.npc.Parent then
				mk.npc:Destroy()
			end
			mk.npc = nil
		elseif not mk.npc and not mk.busy and d < NEAR and made < PER_TICK then
			made += 1
			mk.busy = true
			task.spawn(function()
				local ok, err = pcall(spawnAt, mk)
				if not ok then
					warn("Staff: " .. tostring(err))
				end
				mk.busy = false
			end)
		end
	end
	task.wait(made > 0 and 0.3 or 1.2)
end
