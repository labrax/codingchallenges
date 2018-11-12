file <- readLines("stdin", n=1)

df <- read.csv(file)

#PART A
## compute the distance to each row to 0,0,0 print using cat(distance_i, "\n")
for(i in 1:nrow(df)) {
	    distance_i <- df[i,]$X1*df[i,]$X1 + df[i,]$X2*df[i,]$X2 + df[i,]$X3*df[i,]$X3
    cat(distance_i, "\n")
}

#PART B
## give the prediction (Y) for K = 1
min <- 0
min_val <- 999

for(i in 1:nrow(df)) {
    distance_i <- df[i,]$X1*df[i,]$X1 + df[i,]$X2*df[i,]$X2 + df[i,]$X3*df[i,]$X3
    if(distance_i < min_val) {
        min <- i
        min_val <- distance_i
    }
}

prediction <- df[min,]$Y
cat(as.character(prediction), "\n")

#PART C
##give the prediction (Y) for K = 3
df$distance <- df$X1*df$X1 + df$X2*df$X2 + df$X3*df$X3
ordered <- df[order(df$distance),]
top3_most <- table(ordered[c(1:3),]$Y)

value <- names(which.max(top3_most))

cat(value, "\n")

