# dfg-rating: adding international network
thie branch is to create country network (with several divisions inside) and international network (with several countries inside) for the dfg_rating project.

## national network
designed based on the ClusteredNetwork(). To give a real trend to all teams, there are 4 league divisions(clusters) in the network, each division has a true rating trend.\\
The network was created as a full connected double round-robin at first, then use 'active' or 'inactive' to lable if a match happens or not. \\
Inside each division, the match type called 'League', it's a double round robin. Between different division, it is a one leg 'national' match controled by a prob. All edges related to '4-th' division are 'inacitve'.\\
After each season, teams are relegated/promoted by the end-of-season points (called ranking in the code) they get. And there are 3-modes to give promoted/relegated teams a rating for next season:\\
For example, team A, B, C are from division 1 with end-of-season rating 9, 10, 11. team X, Y, Z from division 2 with end-of-season points 2, 4, 6. team A B relegated, team X Z promoted.\\
1. keep: A, B, X, Z still keep their end-of-season rank and their original trends.\\
2. mix:A, B will have rating + mean rating difference of two divisions. In this example, mean of division 1 is 10, mean rating of division 2 is 4. So A will get a 9-(10-4)=3, X will get a 2+(10-4)=8. And they will continue with new division's rating trends.\\
3. interchange:the mean rating of promoted teams is mean(2+6)=3. Then A and B will get a new rating that keeps new_A:new_B = A:B, also the mean(new_A, new_B)=3, which is new_A = 3/(9+10)

## international network
The international network will create country network first. Then it will count team numbers and create a big network. For instance, 3 country with 20 teams in each, then the international network will create a 3*20=60 nodes network, and mapping, combine the country network to this big network.\\
After create the graph, the network will choose teams to attend international match by randomly or by the top end-of-season points from each country's 1st division.\\
The season 0 does not have international match, since we can just know which team we need to pick at the end of season 0, so the international match will scheduled to season 1.\\
The 'international' match are two legs with a prob. controls it happen or not.\\
Then, the rating of those teams who join international match are choosen from the latest avaliable date. For instance, team A from country 0, with 3 days between league match, competes team B from country 1, with 10 days between league match, the international competition happends at day 11, season 1. For team A, the rating of day 11 choose from day 10 (1+3+3+3), which is the 4-th round. But the rating of team B choosen from day 11 (1+10), which is the 2nd round.\\

