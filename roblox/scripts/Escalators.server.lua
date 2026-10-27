-- Escalator treads are anchored parts with a surface velocity, so anyone standing
-- on one is carried up the slope (you can still walk down against it).
local SPEED = 5

for _, part in ipairs(workspace.Mall.Escalators:GetDescendants()) do
	if part:IsA("BasePart") and part.Name == "Tread" then
		part.AssemblyLinearVelocity = part.CFrame.XVector * SPEED
	end
end
