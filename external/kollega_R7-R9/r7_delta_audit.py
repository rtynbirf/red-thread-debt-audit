# R7-v0.1 operational audit
# Recomputes the explicitly defined Δ6, Δ11 and r_marg from the recovered R7 facts.
delta6 = [1, 0, 0, 0, 1, 0]
chain11 = [1,1,1,1,0,0,1,0,0,1,0]
Delta6 = sum(delta6)/len(delta6)
Delta11 = sum(chain11)/len(chain11)
r_marg = 2/5
print({"Delta6": Delta6, "Delta11": Delta11, "r_marg": r_marg})
