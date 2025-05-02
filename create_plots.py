import pandas
import matplotlib.pyplot as plt

METRICS = ["fitness", "precision", "generalization"]

FILES = ["conformance_polluted_values_medium", "conformance_polluted_values_small"]

for file in FILES:
    polluted_df = pandas.read_csv(file+".csv")

    print(polluted_df)

    group_dfs = polluted_df.groupby(["pollution_type","noise"])
    for key, item in group_dfs:
        current = group_dfs.get_group(key)
        for m in METRICS:
            metric = [current.groupby(["percentage"]).get_group(k)[m] for k,v in current.groupby(["percentage"])]
            #print(group_dfs.get_group(key), "\n\n"
            #print(fitness)

            plt.boxplot(metric)
            plt.title(str(key) + " " + m)
            plt.ylim(-0.1,1.1)
            plt.savefig(file+"_"+m+"_"+str(key)+".pdf", format="pdf")
            plt.show()