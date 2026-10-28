-- Every lift in the city: the mall's glass lift, the office and apartment lifts and the
-- tower express lifts. Each is a Model named Elevator with a Stops folder (NumberValues 1..n
-- holding floor heights), a Car and a Landings folder (Door<i>, Call<i>, Display<i>).
--
-- The server decides where each car goes and when, and publishes that as attributes on the
-- model. It never moves the car itself: every player's screen draws the car from those
-- attributes (Elevators.client), which keeps the ride smooth instead of stuttering at the
-- network rate.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Motion = require(ReplicatedStorage:WaitForChild("ElevatorMotion"))

local DOOR_TIME = 1.0 -- seconds for the doors to open or close
local DWELL = 5 -- seconds the doors stay open
local now = function()
	return workspace:GetServerTimeNow()
end

local remote = Instance.new("RemoteEvent")
remote.Name = "ElevatorRequest"
remote.Parent = ReplicatedStorage

local lifts = {}

local function doorFraction(e, t)
	local s = math.clamp((t - e.doorT) / DOOR_TIME, 0, 1)
	return e.doorOpen and s or 1 - s
end

local function setDoors(e, open)
	if e.doorOpen == open then
		return
	end
	local t = now()
	local f = doorFraction(e, t)
	-- start the new motion from wherever the doors are now, so a reopen never jumps
	e.doorT = open and t - f * DOOR_TIME or t - (1 - f) * DOOR_TIME
	e.doorOpen = open
	e.model:SetAttribute("DoorT", e.doorT)
	e.model:SetAttribute("DoorOpen", open)
	if open then
		e.openedAt = t
	end
end

local function nearest(e, from, step)
	local i = from + step
	while i >= 1 and i <= #e.stops do
		if e.requests[i] then
			return i
		end
		i += step
	end
	return nil
end

-- the next floor to visit: keep going the way the car is going while anyone wants a floor
-- that way, then turn round
local function pick(e)
	if e.requests[e.floor] then
		return e.floor
	end
	local first, second = 1, -1
	if e.dir < 0 then
		first, second = -1, 1
	end
	local target = nearest(e, e.floor, first)
	if target then
		e.dir = first
		return target
	end
	target = nearest(e, e.floor, second)
	if target then
		e.dir = second
		return target
	end
	e.dir = 0
	return nil
end

local function holdOpen(e)
	while now() - e.openedAt < DWELL do
		task.wait(0.1)
	end
end

local function run(e)
	while true do
		local target = pick(e)
		if target == e.floor then
			e.requests[target] = nil
			setDoors(e, true)
			holdOpen(e)
		elseif target then
			setDoors(e, false)
			task.wait(DOOR_TIME + 0.35)
			if e.requests[e.floor] then
				continue -- somebody called it back to this floor while the doors were closing
			end
			local from, to = e.stops[e.floor], e.stops[target]
			local plan = Motion.plan(from, to, e.vmax)
			local start = now() + 0.15
			e.model:SetAttribute("Target", target)
			e.model:SetAttribute("From", from)
			e.model:SetAttribute("To", to)
			e.model:SetAttribute("Start", start)
			task.wait(start + plan.duration - now())
			e.floor = target
			e.requests[target] = nil
			e.model:SetAttribute("Floor", target)
			e.model:SetAttribute("Arrivals", (e.model:GetAttribute("Arrivals") or 0) + 1)
			setDoors(e, true)
			holdOpen(e)
		else
			if e.doorOpen and now() - e.openedAt >= DWELL then
				setDoors(e, false)
			end
			task.wait(0.15)
		end
	end
end

local function request(e, i)
	if not e.stops[i] then
		return
	end
	if i == e.floor and e.doorOpen then
		e.openedAt = now() -- already here with the doors open: keep them open a little longer
		return
	end
	e.requests[i] = true
end

local function setup(model)
	local stopsFolder = model:FindFirstChild("Stops")
	local car = model:FindFirstChild("Car")
	local floor = car and car:FindFirstChild("Floor")
	if not stopsFolder or not floor then
		return
	end
	local stops = {}
	for i = 1, #stopsFolder:GetChildren() do
		local v = stopsFolder:FindFirstChild(tostring(i))
		if not v then
			break
		end
		stops[i] = v.Value
	end
	local speed = model:FindFirstChild("MaxSpeed")
	local e = {
		model = model,
		stops = stops,
		vmax = speed and speed.Value or 14,
		floor = 1,
		dir = 0,
		requests = {},
		doorOpen = false,
		doorT = 0,
		openedAt = 0,
		-- the car never moves on the server, so its floor marks the shaft for checking requests
		footprint = floor.CFrame,
		size = floor.Size,
	}
	model:SetAttribute("Floor", 1)
	model:SetAttribute("Target", 1)
	model:SetAttribute("From", stops[1])
	model:SetAttribute("To", stops[1])
	model:SetAttribute("Start", 0)
	model:SetAttribute("DoorOpen", false)
	model:SetAttribute("DoorT", 0)
	model:SetAttribute("Arrivals", 0)
	lifts[model] = e

	local landings = model:FindFirstChild("Landings")
	for i = 1, #stops do
		local call = landings and landings:FindFirstChild("Call" .. i)
		local prompt = call and call:FindFirstChildOfClass("ProximityPrompt")
		if prompt then
			prompt.Triggered:Connect(function()
				request(e, i)
			end)
		end
	end
	task.spawn(run, e)
end

for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("Model") and d.Name == "Elevator" then
		setup(d)
	end
end

-- buttons on the panel a player sees inside a car
remote.OnServerEvent:Connect(function(player, model, action, index)
	local e = typeof(model) == "Instance" and lifts[model]
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not e or not root then
		return
	end
	local rel = e.footprint:PointToObjectSpace(root.Position)
	local lo, hi = e.stops[1], e.stops[#e.stops]
	if math.abs(rel.X) > e.size.X / 2 + 4 or math.abs(rel.Z) > e.size.Z / 2 + 4 then
		return
	end
	if root.Position.Y < lo - 8 or root.Position.Y > hi + 20 then
		return
	end
	if action == "go" and typeof(index) == "number" then
		request(e, math.floor(index))
	elseif action == "open" then
		local m = e.model
		local plan = Motion.plan(m:GetAttribute("From"), m:GetAttribute("To"), e.vmax)
		if m:GetAttribute("Start") + plan.duration < now() then
			request(e, e.floor)
		end
	elseif action == "close" and e.doorOpen then
		e.openedAt = now() - DWELL
	end
end)
