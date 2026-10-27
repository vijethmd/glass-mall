-- City traffic: cars loop round the ring highway and run up and down the boulevard, two
-- avenues and a street. They keep left, as in Bengaluru, and wrap round at the ends.
local RunService = game:GetService("RunService")

local PATHS = __PATHS__ -- points in studs, loop?, lanes { offset right of the path, direction }, cars, speed
local CAR_Y = __CAR_Y__
local UP = Vector3.new(0, 1, 0)

for _, path in ipairs(PATHS) do
	if path.loop then
		table.insert(path.pts, path.pts[1])
	end
	path.cum = { 0 }
	for i = 2, #path.pts do
		path.cum[i] = path.cum[i - 1] + (path.pts[i] - path.pts[i - 1]).Magnitude
	end
	path.length = path.cum[#path.cum]
end

-- position and direction at distance s along a path
local function sample(path, s)
	local pts, cum = path.pts, path.cum
	local lo, hi = 1, #pts
	while hi - lo > 1 do
		local mid = (lo + hi) // 2
		if cum[mid] <= s then
			lo = mid
		else
			hi = mid
		end
	end
	local span = cum[hi] - cum[lo]
	local a = span > 0 and (s - cum[lo]) / span or 0
	return pts[lo]:Lerp(pts[hi], a), (pts[hi] - pts[lo]).Unit
end

local rng = Random.new(3)
local models = workspace.Site.Traffic:GetChildren()
local cars = {}
for _, path in ipairs(PATHS) do
	for i = 1, path.count do
		local model = table.remove(models)
		if not model then
			break
		end
		local lane = path.lanes[(i - 1) % #path.lanes + 1]
		table.insert(cars, {
			model = model,
			path = path,
			s = rng:NextNumber(0, path.length),
			offset = lane[1],
			dir = lane[2],
			speed = path.speed * rng:NextNumber(0.85, 1.1),
		})
	end
end

RunService.Heartbeat:Connect(function(dt)
	for _, car in ipairs(cars) do
		local path = car.path
		car.s = (car.s + car.dir * car.speed * dt) % path.length
		local pos, dir = sample(path, car.s)
		pos = pos + dir:Cross(UP) * car.offset + Vector3.new(0, CAR_Y, 0)
		car.model:PivotTo(CFrame.lookAt(pos, pos + dir * car.dir))
	end
end)
