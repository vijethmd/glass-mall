-- Animates the LED walls, cinema screens and arcade marquees, spins the coins and the car
-- showroom turntables, flashes the sky club's dance floor and makes trampolines bounce, on
-- each player's screen.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local player = Players.LocalPlayer
local DANCE = {
	Color3.fromRGB(255, 60, 160),
	Color3.fromRGB(60, 200, 255),
	Color3.fromRGB(255, 200, 40),
	Color3.fromRGB(140, 80, 255),
	Color3.fromRGB(60, 255, 140),
}

local coins = workspace:WaitForChild("Coins")
local home = setmetatable({}, { __mode = "k" }) -- each coin's resting position

local gradients, spins, tiles = {}, {}, {}

local function bounce(hit)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root and hit:IsDescendantOf(character) and root.AssemblyLinearVelocity.Y < 30 then
		local v = root.AssemblyLinearVelocity
		root.AssemblyLinearVelocity = Vector3.new(v.X, 78, v.Z)
	end
end

local function track(d)
	if d:IsA("UIGradient") and d.Name == "Anim" then
		table.insert(gradients, d)
	elseif d:IsA("Model") and d.Name == "Spin" then
		table.insert(spins, d)
	elseif d:IsA("BasePart") and d.Name == "DanceTile" then
		table.insert(tiles, d)
	elseif d:IsA("BasePart") and d.Name == "Trampoline" then
		d.Touched:Connect(bounce)
	end
end
for _, d in ipairs(workspace:GetDescendants()) do
	track(d)
end
workspace.DescendantAdded:Connect(track)

local t = 0
RunService.RenderStepped:Connect(function(dt)
	t = t + dt
	for i = #gradients, 1, -1 do
		local g = gradients[i]
		if g.Parent then
			g.Rotation = (t * 18 + i * 40) % 360
			g.Offset = Vector2.new(math.sin(t * 0.5 + i) * 0.4, 0)
		else
			table.remove(gradients, i)
		end
	end
	for i = #spins, 1, -1 do
		local m = spins[i]
		local table_ = m.Parent and m:FindFirstChild("Turntable")
		if table_ then
			local c = table_.Position
			m:PivotTo(CFrame.new(c) * CFrame.Angles(0, dt * 0.35, 0) * CFrame.new(-c) * m:GetPivot())
		elseif not m.Parent then
			table.remove(spins, i)
		end
	end
	for i, coin in ipairs(coins:GetChildren()) do
		local p = home[coin]
		if not p then
			p = coin.Position
			home[coin] = p
		end
		coin.CFrame = CFrame.new(p + Vector3.new(0, math.sin(t * 2 + i) * 0.4, 0)) * CFrame.Angles(0, t * 2.5 + i, 0)
	end
end)

task.spawn(function()
	while true do
		for i = #tiles, 1, -1 do
			local tile = tiles[i]
			if tile.Parent then
				tile.Color = DANCE[math.random(#DANCE)]
			else
				table.remove(tiles, i)
			end
		end
		task.wait(0.45)
	end
end)
