-- The explorer passport: every shop, office floor, flat, sky lounge, house and landmark in
-- Glass City is a stamp (CityData.DISCOVERIES). Walk into a new one and your screen asks for
-- a stamp; the server checks you are really there, adds it, pays 3 coins and saves your
-- passport between visits. "Places" on the leaderboard is how many stamps you have.
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CityData = require(ReplicatedStorage:WaitForChild("CityData"))
local remote = ReplicatedStorage:WaitForChild("Passport")
local REWARD, SLACK = 3, 6 -- coins per new stamp; studs of leeway when checking where you are

local store = nil
pcall(function()
	store = DataStoreService:GetDataStore("GlassCityPassport")
end)

local books = {} -- player -> { [key] = true }
local dirty = {}

local function count(book)
	local n = 0
	for _ in pairs(book) do
		n += 1
	end
	return n
end

local function load(player)
	local book = {}
	if store then
		local ok, saved = pcall(function()
			return store:GetAsync("u" .. player.UserId)
		end)
		if ok and type(saved) == "table" then
			for _, key in ipairs(saved) do
				if type(key) == "string" then
					book[key] = true
				end
			end
		end
	end
	return book
end

local function save(player)
	local book = books[player]
	if not store or not book or not dirty[player] then
		return
	end
	local list = {}
	for key in pairs(book) do
		table.insert(list, key)
	end
	local ok = pcall(function()
		store:SetAsync("u" .. player.UserId, list)
	end)
	if ok then
		dirty[player] = nil
	end
end

local function near(d, p)
	return p.X >= d[3] - SLACK and p.X <= d[5] + SLACK and p.Z >= d[4] - SLACK and p.Z <= d[6] + SLACK
		and p.Y >= d[7] - SLACK and p.Y <= d[8] + SLACK
end

local function join(player)
	local stats = player:WaitForChild("leaderstats", 30)
	local places = Instance.new("IntValue")
	places.Name = "Places"
	local book = load(player)
	books[player] = book
	places.Value = count(book)
	if stats then
		places.Parent = stats
	end
	local list = {}
	for key in pairs(book) do
		table.insert(list, key)
	end
	remote:FireClient(player, "book", list, #CityData.KEYS)
end
Players.PlayerAdded:Connect(join)
for _, player in ipairs(Players:GetPlayers()) do
	task.spawn(join, player)
end

remote.OnServerEvent:Connect(function(player, action, index)
	local book = books[player]
	if not book then
		return
	end
	if action == "sync" then -- the screen asks again for its book (e.g. after it reloads)
		local list = {}
		for key in pairs(book) do
			table.insert(list, key)
		end
		remote:FireClient(player, "book", list, #CityData.KEYS)
		return
	end
	if action ~= "visit" or type(index) ~= "number" then
		return
	end
	local d = CityData.DISCOVERIES[index]
	local key = CityData.KEY_OF[index]
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not d or not key or book[key] or not root or not near(d, root.Position) then
		return
	end
	book[key] = true
	dirty[player] = true
	local n = count(book)
	local stats = player:FindFirstChild("leaderstats")
	if stats then
		local places, coins = stats:FindFirstChild("Places"), stats:FindFirstChild("Coins")
		if places then
			places.Value = n
		end
		if coins then
			coins.Value += REWARD
		end
	end
	remote:FireClient(player, "stamp", key, d[1], d[2], n, #CityData.KEYS, REWARD)
end)

Players.PlayerRemoving:Connect(function(player)
	save(player)
	books[player] = nil
	dirty[player] = nil
end)

game:BindToClose(function()
	for _, player in ipairs(Players:GetPlayers()) do
		save(player)
	end
end)

task.spawn(function() -- save now and then too, in case a server stops without warning
	while true do
		task.wait(120)
		for _, player in ipairs(Players:GetPlayers()) do
			save(player)
		end
	end
end)
