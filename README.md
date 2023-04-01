Main purpose of this project is to get price differences for different currencies. Similiar to steamdb. Currently you can feed the function list of appids manually or you can use a category and it will fetch the price differences for these games from steam.  


Snapshot of steam price differences on Spring Sale 2023. (Calculated for Turkish Lira and USD.)
![image](https://user-images.githubusercontent.com/13971617/229299646-73587270-ca52-4b90-987d-632d6e758bcc.png)
(Price difference is represented in bar, full bar is %1000 cheaper for Turkish lira)


You can set filters, and sort the table on the notion page bellow: 
https://faytan.notion.site/c2b72e79ca964000bd647f1652c838c8

Todos: 

1. Finish front-end for this project using flask. And add option to fetch steam wishlisted games for a user.
2. Save the prices & game names to a database to optimize api fetching.
3. Deploy online so anyone can use this tool online
