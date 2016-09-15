# Should include
#	- Simulating data for a specific node
# 	- Node = {id, power, time, flexible, category, priority, group id}

# Should have the following variables:
# ID/Name
# Power - Watt
# Time - If battery charge or runtime to heat up the house, how long time to load?
# Flexible - Can you schedule it? String with “on”,”flex” or “com”(case of emergency). If not flexible, maybe unnecessary in case of approaching a peak, switch off only then, like outside-lights or similar
# Category
# Priority - How important it is compared to other products
# Group ID (Fas) - Feature to be able to restrict total consumption at the same phase
