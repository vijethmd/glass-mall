-- Cars drive along the main road in both directions and loop round.
local RunService = game:GetService("RunService")

local START = __ROAD_START__ -- road start, studs
local DIR = __ROAD_DIR__ -- unit vector along the road
local ACROSS = __ROAD_ACROSS__ -- unit vector across the road, away from the mall
local LENGTH = __ROAD_LENGTH__
local LANES = __LANES__ -- offset across the road (studs) and direction (+1 / -1)
local CAR_Y = __CAR_Y__

local rng = Random.new(3)
local cars = {}
for i, model in ipairs(workspace.Site.Cars:GetChildren()) do
	local lane = LANES[(i - 1) % #LANES + 1]
	table.insert(cars, {
		model = model,
		s = rng:NextNumber(0, LENGTH),
		offset = lane[1],
		dir = lane[2],
		speed = rng:NextNumber(32, 48),
	})
end

RunService.Heartbeat:Connect(function(dt)
	for _, car in ipairs(cars) do
		car.s = (car.s + car.dir * car.speed * dt) % LENGTH
		local pos = START + DIR * car.s + ACROSS * car.offset + Vector3.new(0, CAR_Y, 0)
		car.model:PivotTo(CFrame.lookAt(pos, pos + DIR * car.dir))
	end
end)
