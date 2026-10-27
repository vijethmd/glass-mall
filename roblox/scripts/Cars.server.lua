-- Drivable cars. Parked cars wait around the city, and the "Get a car" pads give you
-- your own. Each car is a chassis on four wheels joined by hinge constraints: the
-- front wheels steer with servos and all four are driven by motors that follow the
-- VehicleSeat (W/S or arrow keys to drive, A/D to steer, Space to get out).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")

local spawns = workspace:WaitForChild("CarSpawns")
local folder = Instance.new("Folder")
folder.Name = "DrivableCars"
folder.Parent = workspace

local WHEEL_R = 1.4
local FORWARD = __CAR_FORWARD__ -- motor direction that rolls the car forward
local STEER = __CAR_STEER__ -- servo direction that turns the front wheels left for A
local DRIVE_TORQUE = 7500
local BRAKE_TORQUE = 12000
local COAST_TORQUE = 500

local PAINT = {
	Color3.fromRGB(200, 36, 40), Color3.fromRGB(30, 90, 190), Color3.fromRGB(240, 240, 236), Color3.fromRGB(24, 26, 30),
	Color3.fromRGB(250, 190, 30), Color3.fromRGB(40, 150, 90), Color3.fromRGB(150, 156, 162), Color3.fromRGB(240, 120, 30),
	Color3.fromRGB(110, 60, 170), Color3.fromRGB(20, 160, 180),
}
local STYLES = {
	{ name = "Sedan", length = 15, width = 7, body = 2.2, cabin = { 8.5, 2.3, 0.6 }, top = 95 },
	{ name = "Coupe", length = 14, width = 7.2, body = 1.9, cabin = { 6.5, 1.9, 1.0 }, top = 120 },
	{ name = "Pickup", length = 17, width = 7.6, body = 2.6, cabin = { 6, 2.6, -2.6 }, top = 85 },
}

local rng = Random.new()
local cars = {}
local owned = {}

local function newPart(model, name, size, cf, color, material, props)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.CFrame = cf
	p.Color = color
	p.Material = material or Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if props then
		for k, v in pairs(props) do
			p[k] = v
		end
	end
	p.Parent = model
	return p
end

local function weld(a, b)
	local w = Instance.new("WeldConstraint")
	w.Part0 = a
	w.Part1 = b
	w.Parent = a
end

local function attach(part, name, pos, axis, secondary)
	local a = Instance.new("Attachment")
	a.Name = name
	a.Position = pos
	a.Axis = axis
	a.SecondaryAxis = secondary
	a.Parent = part
	return a
end

local function prompt(seat, action, objectText)
	local p = Instance.new("ProximityPrompt")
	p.ActionText = action
	p.ObjectText = objectText
	p.HoldDuration = 0
	p.MaxActivationDistance = 12
	p.RequiresLineOfSight = false
	p.Parent = seat
	p.Triggered:Connect(function(player)
		local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
		if humanoid and not seat.Occupant and humanoid.Health > 0 then
			humanoid.Sit = false -- out of any other seat first
			task.wait()
			seat:Sit(humanoid)
		end
	end)
	return p
end

local function buildCar(base, style, color, owner)
	local model = Instance.new("Model")
	model.Name = style.name
	local L, W = style.length, style.width
	local baseY = WHEEL_R + 0.3
	local chassis = newPart(model, "Chassis", Vector3.new(W - 1, 0.8, L - 1), base * CFrame.new(0, baseY, 0),
		Color3.fromRGB(30, 30, 34), Enum.Material.Metal)
	chassis.CustomPhysicalProperties = PhysicalProperties.new(2.5, 0.3, 0, 1, 1)
	model.PrimaryPart = chassis

	local bodyY = baseY + 0.4 + style.body / 2
	local shell = {}
	local function shellPart(name, size, offset, colour, material, props)
		local p = newPart(model, name, size, base * offset, colour, material, props)
		p.Massless = true
		weld(chassis, p)
		table.insert(shell, p)
		return p
	end
	local body = shellPart("Body", Vector3.new(W, style.body, L), CFrame.new(0, bodyY, 0), color,
		Enum.Material.SmoothPlastic, { Reflectance = 0.08 })
	local c = style.cabin
	local cabinY = bodyY + style.body / 2 + c[2] / 2
	shellPart("Windows", Vector3.new(W - 0.6, c[2], c[1]), CFrame.new(0, cabinY, c[3]), Color3.fromRGB(28, 34, 42),
		Enum.Material.Glass, { Transparency = 0.25, Reflectance = 0.25, CanCollide = false })
	shellPart("Roof", Vector3.new(W - 0.5, 0.25, c[1] - 0.6), CFrame.new(0, cabinY + c[2] / 2 + 0.12, c[3]), color,
		Enum.Material.SmoothPlastic, { CanCollide = false })
	shellPart("Bumper", Vector3.new(W + 0.2, 0.7, 0.5), CFrame.new(0, baseY + 0.6, -L / 2 - 0.1), Color3.fromRGB(40, 40, 44))
	shellPart("Bumper", Vector3.new(W + 0.2, 0.7, 0.5), CFrame.new(0, baseY + 0.6, L / 2 + 0.1), Color3.fromRGB(40, 40, 44))
	local lamps = {}
	for _, side in ipairs({ -1, 1 }) do
		local head = shellPart("Headlight", Vector3.new(1.4, 0.5, 0.1), CFrame.new(side * (W / 2 - 1), bodyY + 0.3, -L / 2 - 0.05),
			Color3.fromRGB(255, 246, 220), Enum.Material.Neon, { CanCollide = false })
		local beam = Instance.new("SpotLight")
		beam.Face = Enum.NormalId.Front
		beam.Range = 45
		beam.Angle = 70
		beam.Brightness = 3
		beam.Enabled = false
		beam.Parent = head
		table.insert(lamps, beam)
		shellPart("Taillight", Vector3.new(1.4, 0.5, 0.1), CFrame.new(side * (W / 2 - 1), bodyY + 0.3, L / 2 + 0.05),
			Color3.fromRGB(220, 30, 30), Enum.Material.Neon, { CanCollide = false })
	end

	local seat = Instance.new("VehicleSeat")
	seat.Name = "DriveSeat"
	seat.Size = Vector3.new(2, 0.5, 2)
	seat.CFrame = base * CFrame.new(-W / 4 + 0.3, bodyY + style.body / 2 + 0.25, c[3] + 0.6)
	seat.Color = Color3.fromRGB(30, 30, 34)
	seat.HeadsUpDisplay = false
	seat.MaxSpeed = style.top
	seat.Massless = true
	seat.Parent = model
	weld(chassis, seat)
	prompt(seat, "Drive", style.name)
	local passenger = Instance.new("Seat")
	passenger.Name = "PassengerSeat"
	passenger.Size = Vector3.new(2, 0.5, 2)
	passenger.CFrame = base * CFrame.new(W / 4 - 0.3, bodyY + style.body / 2 + 0.25, c[3] + 0.6)
	passenger.Color = Color3.fromRGB(30, 30, 34)
	passenger.Massless = true
	passenger.Parent = model
	weld(chassis, passenger)
	prompt(passenger, "Ride", style.name)

	local motors, servos = {}, {}
	for _, w in ipairs({ { -1, -1 }, { 1, -1 }, { -1, 1 }, { 1, 1 } }) do
		local side, fz = w[1], w[2]
		local pos = Vector3.new(side * (W / 2 - 0.3), WHEEL_R - baseY, fz * (L / 2 - 2.8))
		local wheelCf = chassis.CFrame * CFrame.new(pos)
		local wheel = newPart(model, "Wheel", Vector3.new(1.3, WHEEL_R * 2, WHEEL_R * 2), wheelCf, Color3.fromRGB(26, 26, 28),
			Enum.Material.SmoothPlastic, { Shape = Enum.PartType.Cylinder })
		wheel.CustomPhysicalProperties = PhysicalProperties.new(1, 1.4, 0, 100, 1)
		for _, other in ipairs({ chassis, body }) do -- the wheel sits partly inside both
			local nc = Instance.new("NoCollisionConstraint")
			nc.Part0 = wheel
			nc.Part1 = other
			nc.Parent = wheel
		end
		local holder, holderPos = chassis, pos
		if fz < 0 then
			local knuckle = newPart(model, "Knuckle", Vector3.new(0.6, 0.6, 0.6), wheelCf, Color3.new(0, 0, 0), nil,
				{ Transparency = 1, CanCollide = false })
			local s0 = attach(chassis, "Steer", pos, Vector3.new(0, 1, 0), Vector3.new(1, 0, 0))
			local s1 = attach(knuckle, "Steer", Vector3.zero, Vector3.new(0, 1, 0), Vector3.new(1, 0, 0))
			local steer = Instance.new("HingeConstraint")
			steer.Attachment0 = s0
			steer.Attachment1 = s1
			steer.ActuatorType = Enum.ActuatorType.Servo
			steer.ServoMaxTorque = 1e6
			steer.AngularSpeed = 6
			steer.LimitsEnabled = true
			steer.LowerAngle = -40
			steer.UpperAngle = 40
			steer.Parent = knuckle
			table.insert(servos, steer)
			holder, holderPos = knuckle, Vector3.zero
		end
		local a0 = attach(holder, "Axle", holderPos, Vector3.new(1, 0, 0), Vector3.new(0, 1, 0))
		local a1 = attach(wheel, "Axle", Vector3.zero, Vector3.new(1, 0, 0), Vector3.new(0, 1, 0))
		local motor = Instance.new("HingeConstraint")
		motor.Attachment0 = a0
		motor.Attachment1 = a1
		motor.ActuatorType = Enum.ActuatorType.Motor
		motor.MotorMaxTorque = COAST_TORQUE
		motor.MotorMaxAcceleration = 70
		motor.Parent = wheel
		table.insert(motors, motor)
	end

	model.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
	model.Parent = folder
	local car = {
		model = model, chassis = chassis, seat = seat, passenger = passenger, motors = motors, servos = servos,
		lamps = lamps, style = style, owner = owner, home = base, idle = 0, flipped = 0,
	}
	seat:GetPropertyChangedSignal("Occupant"):Connect(function()
		local humanoid = seat.Occupant
		if not chassis.Parent then
			return
		end
		if humanoid then
			local player = Players:GetPlayerFromCharacter(humanoid.Parent)
			if player then
				pcall(function()
					chassis:SetNetworkOwner(player)
				end)
			end
		else
			pcall(function()
				chassis:SetNetworkOwnershipAuto()
			end)
		end
	end)
	table.insert(cars, car)
	return car
end

local function removeCar(car)
	for i, c in ipairs(cars) do
		if c == car then
			table.remove(cars, i)
			break
		end
	end
	if car.model then
		car.model:Destroy()
	end
end

local function flatCFrame(cf)
	local look = cf.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	if flat.Magnitude < 0.01 then
		flat = Vector3.new(0, 0, -1)
	end
	return CFrame.lookAt(cf.Position, cf.Position + flat.Unit)
end

-- parked cars around the city
for _, marker in ipairs(spawns:GetChildren()) do
	if marker.Name == "Parked" then
		local base = flatCFrame(marker.CFrame) - Vector3.new(0, marker.Size.Y / 2, 0)
		buildCar(base, STYLES[rng:NextInteger(1, #STYLES)], PAINT[rng:NextInteger(1, #PAINT)], nil)
		task.wait()
	end
end

-- "Get a car" pads
for _, pad in ipairs(spawns:GetChildren()) do
	if pad.Name == "Pad" then
		local base = pad:FindFirstChild("Base")
		local point = pad:FindFirstChild("SpawnPoint")
		local p = base and base:FindFirstChildOfClass("ProximityPrompt")
		if p and point then
			local tag = Instance.new("BillboardGui")
			tag.Size = UDim2.fromOffset(180, 44)
			tag.StudsOffset = Vector3.new(0, 7, 0)
			tag.MaxDistance = 260
			tag.LightInfluence = 0
			local text = Instance.new("TextLabel")
			text.Size = UDim2.fromScale(1, 1)
			text.BackgroundTransparency = 1
			text.Font = Enum.Font.GothamBlack
			text.TextScaled = true
			text.TextColor3 = Color3.fromRGB(120, 230, 255)
			text.TextStrokeTransparency = 0.3
			text.Text = "GET A CAR"
			text.Parent = tag
			tag.Parent = base
			p.Triggered:Connect(function(player)
				local character = player.Character
				local humanoid = character and character:FindFirstChildOfClass("Humanoid")
				if not humanoid or humanoid.Health <= 0 then
					return
				end
				if owned[player] then
					removeCar(owned[player])
					owned[player] = nil
				end
				local cf = flatCFrame(point.CFrame) - Vector3.new(0, point.Size.Y / 2, 0)
				local car = buildCar(cf, STYLES[rng:NextInteger(1, #STYLES)], PAINT[rng:NextInteger(1, #PAINT)], player)
				owned[player] = car
				task.wait(0.2)
				if humanoid.Health > 0 then
					humanoid.Sit = false
					car.seat:Sit(humanoid)
				end
			end)
		end
	end
end

Players.PlayerRemoving:Connect(function(player)
	if owned[player] then
		removeCar(owned[player])
		owned[player] = nil
	end
end)

-- driving: follow each VehicleSeat's throttle and steering
RunService.Heartbeat:Connect(function()
	for _, car in ipairs(cars) do
		local chassis, seat = car.chassis, car.seat
		if chassis.Parent then
			local throttle, steer = seat.ThrottleFloat, seat.SteerFloat
			local speed = chassis.AssemblyLinearVelocity:Dot(chassis.CFrame.LookVector)
			local target, torque = 0, COAST_TORQUE
			if throttle ~= 0 then
				if speed * throttle < -4 then
					torque = BRAKE_TORQUE -- pressing against the motion: brake first
				else
					torque = DRIVE_TORQUE
					target = throttle > 0 and car.style.top or -car.style.top * 0.45
				end
			end
			for _, m in ipairs(car.motors) do
				m.MotorMaxTorque = torque
				m.AngularVelocity = FORWARD * target / WHEEL_R
			end
			local maxAngle = 34 - 20 * math.clamp(math.abs(speed) / car.style.top, 0, 1)
			for _, s in ipairs(car.servos) do
				s.TargetAngle = STEER * steer * maxAngle
			end
		end
	end
end)

-- headlights at night, put overturned cars back on their wheels, return abandoned parked cars
while true do
	task.wait(1)
	local t = Lighting.ClockTime
	local night = t < 6.4 or t > 17.6
	for i = #cars, 1, -1 do
		local car = cars[i]
		local chassis = car.chassis
		if not chassis.Parent then
			table.remove(cars, i)
		else
			for _, lamp in ipairs(car.lamps) do
				lamp.Enabled = night
			end
			if chassis.CFrame.UpVector.Y < 0.3 then
				car.flipped = car.flipped + 1
			else
				car.flipped = 0
			end
			if car.flipped >= 3 then
				car.flipped = 0
				local pos = chassis.Position
				chassis.AssemblyLinearVelocity = Vector3.zero
				chassis.AssemblyAngularVelocity = Vector3.zero
				car.model:PivotTo(flatCFrame(CFrame.lookAt(pos, pos + chassis.CFrame.LookVector)) + Vector3.new(0, 5, 0))
			end
			if car.seat.Occupant or car.passenger.Occupant then
				car.idle = 0
			else
				car.idle = car.idle + 1
			end
			if not car.owner and car.idle > 120 and (chassis.Position - car.home.Position).Magnitude > 60 then
				car.idle = 0
				chassis.AssemblyLinearVelocity = Vector3.zero
				chassis.AssemblyAngularVelocity = Vector3.zero
				car.model:PivotTo(car.home * CFrame.new(0, WHEEL_R + 0.3, 0))
			end
		end
	end
end
