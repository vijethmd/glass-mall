-- Arcade machines you can play: every screen with an Arcade StringValue (the mall's 3F
-- arcade, Pixel Arcade, the game studio and the console shop) runs one of three games:
--   catch   Coin Catch: move the basket, catch falling coins (25 seconds)
--   dash    Glass Dash: jump the glass shards for as long as you can
--   memory  Memory Lights: repeat the flashing pads, one more each round
-- Mouse, keys and touch all work. Good scores earn coins (checked by Arcade.server).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local player = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("Arcade")
local TITLES = { catch = "COIN CATCH", dash = "GLASS DASH", memory = "MEMORY LIGHTS" }
local HELP = {
	catch = "Move with the mouse, your finger or A / D. Gold coins are worth 3.",
	dash = "Click, tap or press Space to jump the shards.",
	memory = "Watch the pads light up, then press them in the same order.",
}
local playing = false

-- ------------------------------------------------------------------ the cabinet screen
local gui = Instance.new("ScreenGui")
gui.Name = "Arcade"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 20
gui.Enabled = false
gui.Parent = player:WaitForChild("PlayerGui")

local dim = Instance.new("Frame")
dim.Size = UDim2.fromScale(1, 1)
dim.BackgroundColor3 = Color3.new(0, 0, 0)
dim.BackgroundTransparency = 0.35
dim.Parent = gui

local cab = Instance.new("Frame")
cab.AnchorPoint = Vector2.new(0.5, 0.5)
cab.Position = UDim2.fromScale(0.5, 0.5)
cab.Size = UDim2.fromOffset(520, 420)
cab.BackgroundColor3 = Color3.fromRGB(20, 18, 34)
cab.Parent = gui
Instance.new("UICorner", cab).CornerRadius = UDim.new(0, 18)
local cabStroke = Instance.new("UIStroke", cab)
cabStroke.Thickness = 3
cabStroke.Color = Color3.fromRGB(160, 90, 255)
local fit = Instance.new("UIScale", cab)

local head = Instance.new("TextLabel")
head.Size = UDim2.new(1, -40, 0, 40)
head.Position = UDim2.fromOffset(20, 10)
head.BackgroundTransparency = 1
head.Font = Enum.Font.Arcade
head.TextSize = 30
head.TextColor3 = Color3.fromRGB(255, 220, 90)
head.TextXAlignment = Enum.TextXAlignment.Left
head.Parent = cab

local scoreLabel = Instance.new("TextLabel")
scoreLabel.Size = UDim2.new(0, 200, 0, 40)
scoreLabel.Position = UDim2.new(1, -220, 0, 10)
scoreLabel.BackgroundTransparency = 1
scoreLabel.Font = Enum.Font.Arcade
scoreLabel.TextSize = 26
scoreLabel.TextColor3 = Color3.fromRGB(120, 240, 255)
scoreLabel.TextXAlignment = Enum.TextXAlignment.Right
scoreLabel.Parent = cab

local screen = Instance.new("Frame")
screen.Position = UDim2.fromOffset(20, 56)
screen.Size = UDim2.new(1, -40, 1, -110)
screen.BackgroundColor3 = Color3.fromRGB(8, 10, 24)
screen.ClipsDescendants = true
screen.Parent = cab
Instance.new("UICorner", screen).CornerRadius = UDim.new(0, 10)

local foot = Instance.new("TextLabel")
foot.Size = UDim2.new(1, -150, 0, 40)
foot.Position = UDim2.new(0, 20, 1, -48)
foot.BackgroundTransparency = 1
foot.Font = Enum.Font.Gotham
foot.TextSize = 14
foot.TextWrapped = true
foot.TextXAlignment = Enum.TextXAlignment.Left
foot.TextColor3 = Color3.fromRGB(200, 200, 220)
foot.Parent = cab

local quit = Instance.new("TextButton")
quit.Size = UDim2.fromOffset(110, 36)
quit.Position = UDim2.new(1, -130, 1, -46)
quit.BackgroundColor3 = Color3.fromRGB(60, 40, 90)
quit.Font = Enum.Font.GothamBold
quit.TextSize = 15
quit.TextColor3 = Color3.new(1, 1, 1)
quit.Text = "Leave"
quit.Parent = cab
Instance.new("UICorner", quit).CornerRadius = UDim.new(0, 10)

local function resize()
	local v = workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize or Vector2.new(1024, 768)
	fit.Scale = math.min(1, (v.X - 24) / 520, (v.Y - 24) / 420)
end
resize()
if workspace.CurrentCamera then
	workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(resize)
end

local function box(parent, x, y, w, h, color, round)
	local f = Instance.new("Frame")
	f.Position = UDim2.fromOffset(x, y)
	f.Size = UDim2.fromOffset(w, h)
	f.BackgroundColor3 = color
	f.BorderSizePixel = 0
	f.Parent = parent
	if round then
		Instance.new("UICorner", f).CornerRadius = UDim.new(round, 0)
	end
	return f
end

local function clear()
	for _, c in ipairs(screen:GetChildren()) do
		if not c:IsA("UICorner") then
			c:Destroy()
		end
	end
end

local function banner(text, sub)
	local t = Instance.new("TextLabel")
	t.Size = UDim2.fromScale(1, 0.4)
	t.Position = UDim2.fromScale(0, 0.22)
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.Arcade
	t.TextSize = 34
	t.TextColor3 = Color3.fromRGB(255, 220, 90)
	t.Text = text
	t.Parent = screen
	if sub then
		local s = t:Clone()
		s.Position = UDim2.fromScale(0, 0.55)
		s.Size = UDim2.fromScale(1, 0.2)
		s.TextSize = 18
		s.Font = Enum.Font.GothamMedium
		s.TextColor3 = Color3.fromRGB(200, 220, 240)
		s.Text = sub
		s.Parent = screen
	end
end

local quitting = false
quit.Activated:Connect(function()
	quitting = true
end)

local function size()
	return screen.AbsoluteSize.X / fit.Scale, screen.AbsoluteSize.Y / fit.Scale
end

-- ------------------------------------------------------------------ Coin Catch
local function playCatch(setScore)
	local W, H = size()
	local basket = box(screen, W / 2 - 40, H - 26, 80, 16, Color3.fromRGB(120, 240, 255), 0.4)
	local bx, score, coins, t, spawnT = W / 2, 0, {}, 0, 0
	local left, right = false, false
	local c1 = UserInputService.InputBegan:Connect(function(i)
		if i.KeyCode == Enum.KeyCode.A or i.KeyCode == Enum.KeyCode.Left then
			left = true
		elseif i.KeyCode == Enum.KeyCode.D or i.KeyCode == Enum.KeyCode.Right then
			right = true
		end
	end)
	local c2 = UserInputService.InputEnded:Connect(function(i)
		if i.KeyCode == Enum.KeyCode.A or i.KeyCode == Enum.KeyCode.Left then
			left = false
		elseif i.KeyCode == Enum.KeyCode.D or i.KeyCode == Enum.KeyCode.Right then
			right = false
		end
	end)
	local pointer = nil
	local c3 = UserInputService.InputChanged:Connect(function(i)
		if i.UserInputType == Enum.UserInputType.MouseMovement or i.UserInputType == Enum.UserInputType.Touch then
			pointer = (i.Position.X - screen.AbsolutePosition.X) / fit.Scale
		end
	end)
	while t < 25 and not quitting do
		local dt = RunService.RenderStepped:Wait()
		t += dt
		if pointer then
			bx = bx + (math.clamp(pointer, 40, W - 40) - bx) * math.min(1, dt * 14)
		end
		bx = math.clamp(bx + ((right and 1 or 0) - (left and 1 or 0)) * 420 * dt, 40, W - 40)
		basket.Position = UDim2.fromOffset(bx - 40, H - 26)
		spawnT -= dt
		if spawnT <= 0 then
			spawnT = math.max(0.22, 0.6 - t * 0.014)
			local gold = math.random() < 0.15
			local c = box(screen, math.random(10, W - 30), -20, gold and 22 or 16, gold and 22 or 16,
				gold and Color3.fromRGB(255, 200, 40) or Color3.fromRGB(255, 236, 140), 0.5)
			table.insert(coins, { f = c, x = c.Position.X.Offset, y = -20, v = 120 + t * 9 + math.random(0, 60), gold = gold })
		end
		for i = #coins, 1, -1 do
			local c = coins[i]
			c.y += c.v * dt
			c.f.Position = UDim2.fromOffset(c.x, c.y)
			if c.y > H - 34 and c.y < H - 10 and math.abs(c.x + 8 - bx) < 48 then
				score += c.gold and 3 or 1
				setScore(score)
				c.f:Destroy()
				table.remove(coins, i)
			elseif c.y > H then
				c.f:Destroy()
				table.remove(coins, i)
			end
		end
	end
	c1:Disconnect()
	c2:Disconnect()
	c3:Disconnect()
	return score, t
end

-- ------------------------------------------------------------------ Glass Dash
local function playDash(setScore)
	local W, H = size()
	local ground = H - 40
	box(screen, 0, ground, W, 40, Color3.fromRGB(40, 36, 70))
	local hero = box(screen, 70, ground - 30, 30, 30, Color3.fromRGB(255, 120, 200), 0.2)
	local y, vy, t, score, spawnT, shards = 0, 0, 0, 0, 1.2, {}
	local function jump()
		if y <= 0.01 then
			vy = 560
		end
	end
	local c1 = UserInputService.InputBegan:Connect(function(i)
		if i.KeyCode == Enum.KeyCode.Space or i.KeyCode == Enum.KeyCode.W or i.KeyCode == Enum.KeyCode.Up
			or i.UserInputType == Enum.UserInputType.MouseButton1 or i.UserInputType == Enum.UserInputType.Touch then
			jump()
		end
	end)
	local alive = true
	while alive and t < 90 and not quitting do
		local dt = RunService.RenderStepped:Wait()
		t += dt
		vy -= 1500 * dt
		y = math.max(0, y + vy * dt)
		if y == 0 then
			vy = 0
		end
		hero.Position = UDim2.fromOffset(70, ground - 30 - y)
		local speed = 260 + t * 10
		spawnT -= dt
		if spawnT <= 0 then
			spawnT = math.random(70, 150) / 100 * math.max(0.55, 1 - t / 80)
			local h = math.random(22, 46)
			table.insert(shards, { f = box(screen, W, ground - h, 18, h, Color3.fromRGB(140, 220, 255)), x = W, h = h })
		end
		for i = #shards, 1, -1 do
			local s = shards[i]
			s.x -= speed * dt
			s.f.Position = UDim2.fromOffset(s.x, ground - s.h)
			if s.x < 100 and s.x + 18 > 70 and y < s.h - 4 then
				alive = false
			end
			if s.x < -20 then
				s.f:Destroy()
				table.remove(shards, i)
				score += 1
				setScore(score)
			end
		end
	end
	c1:Disconnect()
	return score, t
end

-- ------------------------------------------------------------------ Memory Lights
local function playMemory(setScore)
	local W, H = size()
	local colours = { Color3.fromRGB(255, 70, 90), Color3.fromRGB(70, 200, 255), Color3.fromRGB(255, 210, 60),
		Color3.fromRGB(90, 230, 120) }
	local pads, pressed = {}, nil
	local pw, ph = (W - 60) / 2, (H - 40) / 2
	for k = 1, 4 do
		local b = Instance.new("TextButton")
		b.Text = ""
		b.AutoButtonColor = false
		b.Position = UDim2.fromOffset(20 + ((k - 1) % 2) * (pw + 20), 14 + math.floor((k - 1) / 2) * (ph + 12))
		b.Size = UDim2.fromOffset(pw, ph)
		b.BackgroundColor3 = colours[k]:Lerp(Color3.new(0, 0, 0), 0.6)
		b.Parent = screen
		Instance.new("UICorner", b).CornerRadius = UDim.new(0.12, 0)
		b.Activated:Connect(function()
			pressed = k
		end)
		pads[k] = b
	end
	local function flash(k, d)
		pads[k].BackgroundColor3 = colours[k]
		task.wait(d)
		pads[k].BackgroundColor3 = colours[k]:Lerp(Color3.new(0, 0, 0), 0.6)
	end
	local seq, score, t0 = {}, 0, os.clock()
	while not quitting do
		table.insert(seq, math.random(1, 4))
		task.wait(0.6)
		for _, k in ipairs(seq) do
			flash(k, math.max(0.22, 0.5 - #seq * 0.02))
			task.wait(0.15)
		end
		for _, want in ipairs(seq) do
			pressed = nil
			local waited = 0
			while not pressed and not quitting and waited < 6 do
				waited += task.wait()
			end
			if pressed ~= want then
				return score, os.clock() - t0
			end
			task.spawn(flash, pressed, 0.15)
		end
		score = #seq
		setScore(score)
	end
	return score, os.clock() - t0
end

local GAMES = { catch = playCatch, dash = playDash, memory = playMemory }

local function run(kind)
	if playing then
		return
	end
	playing, quitting = true, false
	local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
	local speed = humanoid and humanoid.WalkSpeed
	if humanoid then
		humanoid.WalkSpeed = 0
	end
	gui.Enabled = true
	resize()
	head.Text = TITLES[kind]
	foot.Text = HELP[kind]
	scoreLabel.Text = "SCORE 0"
	clear()
	banner(TITLES[kind], "Get ready...")
	remote:FireServer("start", kind)
	task.wait(1.6)
	clear()
	local score, duration = GAMES[kind](function(s)
		scoreLabel.Text = "SCORE " .. s
	end)
	clear()
	if quitting and score == 0 then
		banner("BYE!")
	else
		banner("GAME OVER", "Score " .. score .. "  ·  checking your prize...")
		remote:FireServer("finish", kind, score, duration)
	end
	task.wait(quitting and 0.5 or 2.6)
	gui.Enabled = false
	if humanoid and speed then
		humanoid.WalkSpeed = speed
	end
	playing = false
end

remote.OnClientEvent:Connect(function(kind, coins)
	if kind == "prize" and gui.Enabled then
		clear()
		banner(coins > 0 and ("+" .. coins .. " COINS!") or "TRY AGAIN!", coins > 0 and "Nice playing." or "Score more next time.")
	end
end)

-- ------------------------------------------------------------------ prompts on every screen (they stream in and out)
local function hook(part)
	local tag = part:FindFirstChild("Arcade")
	if not part:IsA("BasePart") or not tag or part:FindFirstChild("PlayPrompt") or not GAMES[tag.Value] then
		return
	end
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "PlayPrompt"
	prompt.ActionText = "Play"
	prompt.ObjectText = TITLES[tag.Value]
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 7
	prompt.RequiresLineOfSight = false
	prompt.Parent = part
	prompt.Triggered:Connect(function()
		task.spawn(run, tag.Value)
	end)
end
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("StringValue") and d.Name == "Arcade" and d.Parent then
		hook(d.Parent)
	end
end
workspace.DescendantAdded:Connect(function(d)
	if d:IsA("StringValue") and d.Name == "Arcade" then
		task.defer(function()
			if d.Parent then
				hook(d.Parent)
			end
		end)
	end
end)
