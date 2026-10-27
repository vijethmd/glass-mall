-- Glass coins all over the city. Walk or drive through one to collect it; it comes back
-- after a while. Your total shows on the leaderboard and is saved between visits.
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")

local RESPAWN = 25
local store = nil
pcall(function()
	store = DataStoreService:GetDataStore("GlassCityCoins")
end)

local function load(player, value)
	if not store then
		return
	end
	local ok, saved = pcall(function()
		return store:GetAsync("u" .. player.UserId)
	end)
	if ok and type(saved) == "number" then
		value.Value = saved
	end
end

local function save(player)
	local stats = player:FindFirstChild("leaderstats")
	local coins = stats and stats:FindFirstChild("Coins")
	if store and coins then
		pcall(function()
			store:SetAsync("u" .. player.UserId, coins.Value)
		end)
	end
end

Players.PlayerAdded:Connect(function(player)
	local stats = Instance.new("Folder")
	stats.Name = "leaderstats"
	local coins = Instance.new("IntValue")
	coins.Name = "Coins"
	coins.Parent = stats
	stats.Parent = player
	load(player, coins)
end)
Players.PlayerRemoving:Connect(save)
game:BindToClose(function()
	for _, player in ipairs(Players:GetPlayers()) do
		save(player)
	end
end)

-- who touched it: a character, or whoever is driving the car that hit it
local function playerFromHit(hit)
	local model = hit:FindFirstAncestorOfClass("Model")
	while model do
		local player = Players:GetPlayerFromCharacter(model)
		if player then
			return player
		end
		local seat = model:FindFirstChild("DriveSeat")
		if seat and seat.Occupant then
			return Players:GetPlayerFromCharacter(seat.Occupant.Parent)
		end
		model = model:FindFirstAncestorOfClass("Model")
	end
	return nil
end

for _, coin in ipairs(workspace.Coins:GetChildren()) do
	if coin:IsA("BasePart") then
		local taken = false
		coin.Touched:Connect(function(hit)
			if taken then
				return
			end
			local player = playerFromHit(hit)
			local stats = player and player:FindFirstChild("leaderstats")
			if not stats then
				return
			end
			taken = true
			stats.Coins.Value = stats.Coins.Value + 1
			coin.Transparency = 1
			task.delay(RESPAWN, function()
				coin.Transparency = 0
				taken = false
			end)
		end)
	end
end
