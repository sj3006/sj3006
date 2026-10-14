import os, json, math, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
erf = np.vectorize(math.erf)
N  = lambda x: 0.5*(1+erf(np.asarray(x)/math.sqrt(2)))
Np = lambda x: np.exp(-np.asarray(x)**2/2)/math.sqrt(2*math.pi)
K = 100.0; DAY = 1/365
def d12(S,T,r,q,s):
    d1 = (np.log(S/K)+(r-q+s*s/2)*T)/(s*np.sqrt(T)); return d1, d1-s*np.sqrt(T)
def delta(S,T,r,q,s,kind="call"):
    d1,_=d12(S,T,r,q,s); return np.exp(-q*T)*N(d1) if kind=="call" else -np.exp(-q*T)*N(-d1)
def gamma(S,T,r,q,s):
    d1,_=d12(S,T,r,q,s); return np.exp(-q*T)*Np(d1)/(S*s*np.sqrt(T))
def color_parts(S,T,r,q,s):
    """Color = dGamma/dt (calendar time), per day. Returns base, drift, convergence, total."""
    d1,d2=d12(S,T,r,q,s); st=s*np.sqrt(T)
    pre = np.exp(-q*T)*Np(d1)/(2*S*T*st)/365
    base = pre*(2*q*T+1)
    drift = pre*(2*(r-q)*T/st)*d1
    conv = pre*(-d2*st/st)*d1
    return base, drift, conv, base+drift+conv
color = lambda *a: color_parts(*a)[3]
R = {}
r0,q0,s0,T0 = 0.05,0.0,0.20,1.0
m = np.linspace(0.5,1.5,2001); S = m*K
def fmt(x): return float(x)

# 1.3 base case
rows=[]
for kind in ["call","put"]:
    for mm in [0.9,1.0,1.1]:
        Sx=mm*K; g0=gamma(Sx,T0,r0,q0,s0); g1=gamma(Sx,T0-DAY,r0,q0,s0)
        rows.append(dict(option=kind,m=mm,g0=fmt(g0),g1=fmt(g1),chg=fmt(g1-g0),color=fmt(color(Sx,T0,r0,q0,s0))))
R["base"]=rows

# 1.4 gamma vs moneyness at maturities
mats=[("1 week",7/365),("1 month",1/12),("3 months",0.25),("1 year",1.0)]
plt.figure(figsize=(7,5))
for lab,T in mats:
    plt.plot(m,gamma(S,T,r0,q0,s0),label=f"T = {lab}")
plt.axvline(1,ls="--",c="grey"); plt.xlabel("Moneyness (S/K)"); plt.ylabel("Gamma (call = put)"); plt.legend()
plt.title("Gamma vs. Moneyness at Different Maturities (σ = 20%, r = 5%, q = 0, K = 100)"); plt.tight_layout()
fig=plt.gcf(); fig.savefig(OUT+"figures/gamma_mats.png",dpi=150); plt.close()
R["gamma_tab"]=[dict(mat=lab,**{str(mm):fmt(gamma(mm*K,T,r0,q0,s0)) for mm in [0.9,1.0,1.1]}) for lab,T in mats]

def stats(c):
    i=np.argmin(c); j=np.argmax(c)
    # sign changes
    sc=[fmt(m[k+1]) for k in range(len(c)-1) if np.sign(c[k])!=np.sign(c[k+1])]
    return dict(min=fmt(c[i]),min_at=fmt(m[i]),max=fmt(c[j]),max_at=fmt(m[j]),cross=sc,atm=fmt(c[1000]))

# Color vs moneyness base
c=color(S,T0,r0,q0,s0)
plt.figure(figsize=(7,5))
plt.plot(m,c,label="Call"); plt.plot(m,c,"--",label="Put")
plt.axhline(0,c="k"); plt.axvline(1,ls="--",c="k")
plt.xlabel("Moneyness (S/K)"); plt.ylabel("Color (change in Gamma per calendar day)")
plt.title("Color vs. Moneyness (T = 1 yr, σ = 20%, r = 5%, q = 0)", pad=16); plt.legend(); plt.tight_layout()
plt.savefig(OUT+"figures/color_m.png",dpi=150); plt.close()
R["color_m"]=stats(c)
# finite-difference check across grid
fd = gamma(S,T0-DAY,r0,q0,s0)-gamma(S,T0,r0,q0,s0)
R["fd_maxerr"]=fmt(np.max(np.abs(fd-c))); R["fd_maxabs"]=fmt(np.max(np.abs(c)))

# components
b,dr,cv,tot=color_parts(S,T0,r0,q0,s0)
plt.figure(figsize=(7,5))
plt.plot(m,b,label="Base (pure decay)"); plt.plot(m,dr,label="Drift"); plt.plot(m,cv,label="Convergence")
plt.plot(m,tot,"k",lw=2,label="Total color"); plt.axhline(0,c="grey",lw=.8); plt.axvline(1,ls="--",c="grey")
plt.xlabel("Moneyness (S/K)"); plt.ylabel("Color (change in Gamma per calendar day)")
plt.title("Components of Color vs. Moneyness (T = 1 yr, σ = 20%, r = 5%, q = 0)", pad=16); plt.legend(); plt.tight_layout()
plt.savefig(OUT+"figures/color_parts.png",dpi=150); plt.close()
R["parts"]={k:stats(v) for k,v in [("base",b),("drift",dr),("conv",cv)]}

# 1.5 maturities
fig,ax=plt.subplots(2,2,figsize=(12,7)); R["mats"]={}
for a,(lab,T) in zip(ax.flat,mats):
    cc=color(S,T,r0,q0,s0); a.plot(m,cc); a.axhline(0,c="grey",lw=.8); a.axvline(1,ls="--",c="grey")
    a.set_title(f"T = {lab}"); a.set_xlabel("Moneyness (S/K)"); a.set_ylabel("Color (per calendar day)")
    R["mats"][lab]=stats(cc)
fig.suptitle("Color vs. Moneyness at Different Maturities (σ = 20%, r = 5%, q = 0)"); fig.tight_layout()
fig.savefig(OUT+"figures/color_mats.png",dpi=150); plt.close()

# 1.6 vs time to maturity
days=np.arange(1,731); Ts=days/365
plt.figure(figsize=(7,5)); R["ttm"]=[]
for mm,lab in [(0.9,"OTM call"),(1.0,"ATM call"),(1.1,"ITM call")]:
    cc=color(mm*K,Ts,r0,q0,s0); plt.plot(days,cc,label=f"S/K = {mm} ({lab})")
    k=np.argmax(np.abs(cc)); sc=[int(days[i+1]) for i in range(len(cc)-1) if np.sign(cc[i])!=np.sign(cc[i+1])]
    R["ttm"].append(dict(m=mm,type=lab.split()[0],d1=fmt(cc[0]),w=fmt(cc[6]),mo=fmt(cc[29]),y=fmt(cc[364]),y2=fmt(cc[729]),
        largest=int(days[k]),largest_val=fmt(cc[k]),sign=sc))
plt.xscale("log"); plt.xticks([1,7,30,91,365,730],["1d","1w","1m","3m","1y","2y"])
plt.axhline(0,c="grey",lw=.8); plt.xlabel("Time to maturity (log scale)"); plt.ylabel("Color (change in Gamma per calendar day)")
plt.title("Color vs. Time to Maturity (σ = 20%, r = 5%, q = 0)", pad=16); plt.legend(); plt.tight_layout()
plt.savefig(OUT+"figures/color_ttm.png",dpi=150); plt.close()
plt.figure(figsize=(7,5))
for mm,lab in [(0.9,"OTM"),(1.1,"ITM")]:
    plt.plot(days,color(mm*K,Ts,r0,q0,s0),label=f"S/K = {mm} ({lab})")
plt.xscale("log"); plt.xticks([1,7,30,91,365,730],["1d","1w","1m","3m","1y","2y"]); plt.axhline(0,c="grey",lw=.8)
plt.xlabel("Time to maturity (log scale)"); plt.ylabel("Color (per calendar day)")
plt.title("Color vs. Time to Maturity, OTM and ITM only (zoom)", pad=16); plt.legend(); plt.tight_layout()
plt.savefig(OUT+"figures/color_ttm_zoom.png",dpi=150); plt.close()

def sweep(name,vals,fn,title,lab):
    plt.figure(figsize=(7,5)); R[name]={}
    for v in vals:
        cc=fn(v); plt.plot(m,cc,label=lab(v)); R[name][lab(v)]=stats(cc)
    plt.axhline(0,c="grey",lw=.8); plt.axvline(1,ls="--",c="grey"); plt.xlabel("Moneyness (S/K)")
    plt.ylabel("Color (change in Gamma per calendar day)"); plt.title(title, pad=16); plt.legend(); plt.tight_layout()
    plt.savefig(OUT+f"figures/{name}.png",dpi=150); plt.close()
sweep("vol",[0.1,0.2,0.4],lambda v:color(S,T0,r0,q0,v),"Color vs. Moneyness at Different Volatilities (T = 1 yr, r = 5%, q = 0)",lambda v:f"σ = {v:.0%}")
sweep("rate",[0.0,0.05,0.10],lambda v:color(S,T0,v,q0,s0),"Color vs. Moneyness at Different Interest Rates (T = 1 yr, σ = 20%, q = 0)",lambda v:f"r = {v:.0%}")
sweep("div",[0.0,0.05,0.10],lambda v:color(S,T0,r0,v,s0),"Color vs. Moneyness at Different Dividend Yields (T = 1 yr, σ = 20%, r = 5%)",lambda v:f"q = {v:.0%}")
# put check with dividends: put gamma via FD of put delta
pd = lambda Sx,T,q: (delta(Sx+0.01,T,r0,q,s0,"put")-delta(Sx-0.01,T,r0,q,s0,"put"))/0.02
R["div_put_diff"]=fmt(np.max(np.abs((pd(S,T0-DAY,0.1)-pd(S,T0,0.1))-color(S,T0,r0,0.1,s0))))
json.dump(R,open(OUT+"results.json","w"),indent=1)
