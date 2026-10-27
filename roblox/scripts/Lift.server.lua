-- The glass lift beside the shops. Click a floor button inside the car, or the
-- call button (or prompt) on any landing. Landing doors open only when the car is there.
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local STOPS = __STOPS__ -- floor tops in studs: GF, 1F, 2F, 3F, 4F
local SPEED = 9
local INFO = TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut)

local lift = workspace.Mall.Lift
local car = lift.Car
local floor = car:WaitForChild("Floor")

local landings = {}
for i = 1, #STOPS do
	local door = lift.Landings:FindFirstChild("Door" .. i)
	if door then
		local l, r, slide = door.L, door.R, door.Slide.Value
		landings[i] = {
			l = l,
			r = r,
			lClosed = l.CFrame,
			rClosed = r.CFrame,
			lOpen = l.CFrame * CFrame.new(-slide, 0, 0),
			rOpen = r.CFrame * CFrame.new(slide, 0, 0),
		}
	end
end

local function setDoors(i, open)
	local d = landings[i]
	if not d then
		return
	end
	TweenService:Create(d.l, INFO, { CFrame = open and d.lOpen or d.lClosed }):Play()
	TweenService:Create(d.r, INFO, { CFrame = open and d.rOpen or d.rClosed }):Play()
end

local current = 1
local moving = false
local queue = {}

local function request(i)
	if i == current and not moving then
		setDoors(current, true)
		return
	end
	for _, q in ipairs(queue) do
		if q == i then
			return
		end
	end
	table.insert(queue, i)
end

local function topOfFloor()
	return floor.Position.Y + floor.Size.Y / 2
end

local function travel(target)
	setDoors(current, false)
	task.wait(1)
	moving = true
	local goal = STOPS[target]
	while true do
		local dt = RunService.Heartbeat:Wait()
		local remaining = goal - topOfFloor()
		if math.abs(remaining) < 0.02 then
			break
		end
		local dir = remaining > 0 and 1 or -1
		local step = dir * math.min(SPEED * dt, math.abs(remaining))
		floor.AssemblyLinearVelocity = Vector3.new(0, dir * SPEED, 0)
		car:PivotTo(car:GetPivot() + Vector3.new(0, step, 0))
	end
	floor.AssemblyLinearVelocity = Vector3.zero
	moving = false
	current = target
end

for _, button in ipairs(car:GetChildren()) do
	local n = tonumber(string.match(button.Name, "^Button(%d)$"))
	local click = button:FindFirstChildOfClass("ClickDetector")
	if n and click then
		click.MouseClick:Connect(function()
			request(n)
		end)
	end
end

for i = 1, #STOPS do
	local call = lift.Landings:FindFirstChild("Call" .. i)
	if call then
		local click = call:FindFirstChildOfClass("ClickDetector")
		local prompt = call:FindFirstChildOfClass("ProximityPrompt")
		if click then
			click.MouseClick:Connect(function()
				request(i)
			end)
		end
		if prompt then
			prompt.Triggered:Connect(function()
				request(i)
			end)
		end
	end
end

setDoors(current, true)
while true do
	if #queue > 0 then
		local target = table.remove(queue, 1)
		if target ~= current then
			travel(target)
		end
		setDoors(current, true)
		task.wait(4)
	else
		task.wait(0.2)
	end
end
