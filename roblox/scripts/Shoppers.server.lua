-- Shoppers arrive from the street, walk into the mall through the automatic doors,
-- visit one to three places (shops, food court, arcade, cinemas, terrace) and walk
-- back out. Each leaves and a new one arrives, so the mall always has some life.
local Players = game:GetService("Players")
local PathfindingService = game:GetService("PathfindingService")

local COUNT = 14
local street = workspace.Waypoints.Street:GetChildren()
local inside = workspace.Waypoints.Inside:GetChildren()
local folder = workspace:FindFirstChild("Shoppers")
local rng = Random.new()

local SKIN = {
	Color3.fromRGB(255, 220, 190), Color3.fromRGB(234, 184, 146), Color3.fromRGB(198, 140, 100),
	Color3.fromRGB(160, 105, 72), Color3.fromRGB(120, 78, 52), Color3.fromRGB(86, 58, 40),
}
local TOPS = {
	Color3.fromRGB(230, 90, 70), Color3.fromRGB(60, 120, 200), Color3.fromRGB(245, 245, 240),
	Color3.fromRGB(40, 44, 52), Color3.fromRGB(240, 190, 60), Color3.fromRGB(90, 170, 120),
	Color3.fromRGB(200, 120, 200), Color3.fromRGB(120, 200, 230),
}
local BOTTOMS = {
	Color3.fromRGB(40, 50, 80), Color3.fromRGB(30, 30, 34), Color3.fromRGB(150, 130, 100),
	Color3.fromRGB(90, 90, 96), Color3.fromRGB(60, 80, 120),
}

local function pick(list)
	return list[rng:NextInteger(1, #list)]
end

local function simpleBody(colour)
	local model = Instance.new("Model")
	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"
	root.Size = Vector3.new(2, 5, 1.4)
	root.Color = colour
	root.Parent = model
	local humanoid = Instance.new("Humanoid")
	humanoid.RigType = Enum.HumanoidRigType.R15
	humanoid.HipHeight = 0
	humanoid.Parent = model
	model.PrimaryPart = root
	return model
end

local function makeShopper(at)
	local desc = Instance.new("HumanoidDescription")
	local skin, top, bottom = pick(SKIN), pick(TOPS), pick(BOTTOMS)
	desc.HeadColor = skin
	desc.LeftArmColor = skin
	desc.RightArmColor = skin
	desc.TorsoColor = top
	desc.LeftLegColor = bottom
	desc.RightLegColor = bottom
	local ok, model = pcall(function()
		return Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15)
	end)
	if not ok or not model then
		model = simpleBody(top)
	end
	model.Name = "Shopper"
	local humanoid = model:FindFirstChildOfClass("Humanoid")
	humanoid.WalkSpeed = rng:NextNumber(7, 10)
	humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	model:PivotTo(CFrame.new(at.Position + Vector3.new(0, 3.2, 0)))
	model.Parent = folder
	local root = model:FindFirstChild("HumanoidRootPart")
	if root then
		pcall(function()
			root:SetNetworkOwner(nil)
		end)
	end
	return model, humanoid
end

local function walkTo(model, humanoid, target)
	local root = model:FindFirstChild("HumanoidRootPart")
	if not root then
		return
	end
	local path = PathfindingService:CreatePath({
		AgentRadius = 1.5,
		AgentHeight = 5,
		AgentCanJump = false,
		WaypointSpacing = 5,
		Costs = { Door = 1 },
	})
	local points = {}
	local ok = pcall(function()
		path:ComputeAsync(root.Position, target)
	end)
	if ok and path.Status == Enum.PathStatus.Success then
		for _, w in ipairs(path:GetWaypoints()) do
			table.insert(points, w.Position)
		end
	else
		points = { target }
	end
	for _, p in ipairs(points) do
		if not model.Parent or humanoid.Health <= 0 then
			return
		end
		humanoid:MoveTo(p)
		if not humanoid.MoveToFinished:Wait() then
			humanoid:MoveTo(p)
			if not humanoid.MoveToFinished:Wait() then
				return
			end
		end
	end
end

local function life()
	while true do
		local model, humanoid = makeShopper(pick(street))
		for _ = 1, rng:NextInteger(1, 3) do
			walkTo(model, humanoid, pick(inside).Position)
			task.wait(rng:NextNumber(3, 9))
		end
		walkTo(model, humanoid, pick(street).Position)
		model:Destroy()
		task.wait(rng:NextNumber(2, 8))
	end
end

for _ = 1, COUNT do
	task.spawn(life)
	task.wait(1.5)
end
