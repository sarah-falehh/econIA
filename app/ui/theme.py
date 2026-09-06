from __future__ import annotations

import html
import streamlit as st


def configure_plotly_theme() -> None:
    """Install one accessible visual language for every Plotly chart."""
    import plotly.graph_objects as go
    import plotly.io as pio

    template = go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, Segoe UI, sans-serif", size=16, color="#102A43"),
            title=dict(font=dict(family="Plus Jakarta Sans, Segoe UI, sans-serif", size=22, color="#0A2540")),
            colorway=["#2563EB", "#FF5F57", "#0EA5A8", "#7C3AED", "#F59E0B", "#16A36A", "#E5488D"],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hoverlabel=dict(bgcolor="#071A33", bordercolor="#274A6B", font=dict(color="#FFFFFF", size=15)),
            legend=dict(bgcolor="rgba(255,255,255,.78)", bordercolor="#DCE5EF", borderwidth=1, font=dict(size=15, color="#102A43")),
            xaxis=dict(gridcolor="#DFE8F2", linecolor="#B7C7D8", tickfont=dict(size=14, color="#102A43"), title_font=dict(size=15, color="#102A43"), zeroline=False),
            yaxis=dict(gridcolor="#DFE8F2", linecolor="#B7C7D8", tickfont=dict(size=14, color="#102A43"), title_font=dict(size=15, color="#102A43"), zeroline=False),
            margin=dict(l=40, r=28, t=64, b=44),
        )
    )
    pio.templates["econia"] = template
    pio.templates.default = "econia"


def inject_theme() -> None:
    st.markdown(r'''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    :root{
      --paper:#F5F8FC;
      --paper-2:#FFFFFF;
      --ink:#173B69;
      --muted:#607286;
      --line:#D7DEE8;
      --cobalt:#1C5FA8;
      --cobalt-soft:#EAF2FB;
      --coral:#A61E24;
      --coral-soft:#F6E3E5;
      --mint:#DCEAF7;
      --lime:#E4EEF8;
      --navy:#123F73;
      --warning:#B36B00;
      --danger:#C51E2A;
      --shadow:0 14px 40px rgba(13,63,117,.08);
      --shadow-xl:0 24px 70px rgba(11,37,66,.14);
      --electric:#2563EB;
      --aqua:#0EA5A8;
    }

    html, body, [class*="css"]{font-family:'Inter',ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:16px;}
    .stApp{
      background:
        linear-gradient(rgba(23,105,176,.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(23,105,176,.018) 1px, transparent 1px),
        var(--paper);
      background-size:32px 32px;
      color:var(--ink);
    }
    .block-container{animation:page-enter .36s cubic-bezier(.2,.75,.3,1) both}
    @keyframes page-enter{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:none}}
    header[data-testid="stHeader"]{background:rgba(247,249,252,.88);backdrop-filter:blur(10px);border-bottom:1px solid rgba(13,63,117,.08)}
    .block-container{max-width:1480px;padding:2.2rem 2.7rem 5rem;}
    p,.stCaption,[data-testid="stMarkdownContainer"] p, label, .stSelectbox label, .stTextInput label{font-size:1rem;}
    h1,h2,h3,h4{font-family:'Plus Jakarta Sans',sans-serif!important;color:var(--ink)!important;letter-spacing:-.04em;font-weight:800!important;}
    p,.stCaption,[data-testid="stMarkdownContainer"] p{color:var(--muted);}
    a{color:var(--cobalt)!important}

    /* SIDEBAR — editorial index */
    [data-testid="stSidebar"]{
      background:linear-gradient(180deg,#071A33 0%,#0B3B68 58%,#0E5577 135%);
      border-right:0;
      box-shadow:12px 0 45px rgba(13,63,117,.12);
    }
    [data-testid="stSidebar"]>div{padding-top:0!important;}
    [data-testid="stSidebar"] *{color:#F6F9FD;}
    .brand-lockup{padding:28px 16px 20px;display:flex;gap:13px;align-items:center;border-bottom:1px solid rgba(255,255,255,.10);margin-bottom:16px;position:relative}
    .brand-lockup:after{content:"LIVE";position:absolute;right:12px;top:12px;color:#BDF5DD;font-size:.58rem;letter-spacing:.13em;font-weight:800;background:#16A36A22;border:1px solid #8EE6BC55;padding:4px 7px;border-radius:99px}
    .brand-seal{width:48px;height:48px;border-radius:15px;background:linear-gradient(145deg,#FF776C,#D93642);display:grid;place-items:center;box-shadow:0 10px 26px rgba(255,95,87,.28),inset 0 0 0 1px rgba(255,255,255,.28);font-family:'Plus Jakarta Sans';font-weight:800;color:white;font-size:1rem;transform:rotate(-4deg)}
    .brand-name{font-family:'Plus Jakarta Sans';font-size:1.22rem;font-weight:800;letter-spacing:-.03em;color:white}.brand-name b{color:#D9E6FF}
    .brand-sub{font-size:.70rem;color:#D1DEED!important;letter-spacing:.15em;text-transform:uppercase;margin-top:4px;font-weight:700}
    .side-section{font-size:.68rem;color:#D3E0EE!important;letter-spacing:.18em;text-transform:uppercase;font-weight:800;margin:24px 14px 10px}
    [data-testid="stSidebar"] .stRadio>div{gap:4px}
    [data-testid="stSidebar"] .stRadio label{
      min-height:50px;padding:12px 15px;border-radius:13px;border:1px solid transparent;transition:.2s cubic-bezier(.2,.8,.2,1);font-weight:700;font-size:1.01rem; color:#F6FAFF;
    }
    [data-testid="stSidebar"] .stRadio label:hover{background:rgba(255,255,255,.09);transform:translateX(5px)}
    [data-testid="stSidebar"] .stRadio label p{font-size:1.04rem!important;color:#EAF1F8!important}
    [data-testid="stSidebar"] .stRadio label:has(input:checked){
      background:linear-gradient(135deg,#FFFFFF,#EEF7FF);border-color:#FFFFFF;color:#123F73!important;box-shadow:0 12px 28px rgba(0,0,0,.18);
    }
    [data-testid="stSidebar"] .stRadio label:has(input:checked) *{color:#0D3F75!important}
    [data-testid="stSidebar"] .stButton>button[kind="primary"]{
      background:var(--coral)!important;color:white!important;border:0!important;border-radius:12px!important;box-shadow:none!important;font-weight:800!important;
    }
    .user-chip{margin:14px 6px 10px;padding:13px 14px;border-top:1px solid rgba(255,255,255,.09);border-bottom:1px solid rgba(255,255,255,.09);background:transparent}
    .user-chip b{font-size:1rem;color:white}.user-chip span{font-size:.8rem;color:#D3E0EE}
    [data-testid="stSidebar"] .stCaption{color:#AEC0D2!important;font-size:.68rem}

    /* HERO — magazine masthead */
    .hero{position:relative;padding:31px 34px 32px;border:1px solid rgba(180,200,220,.72);margin-bottom:24px;border-radius:24px;overflow:hidden;background:radial-gradient(circle at 88% 10%,rgba(37,99,235,.14),transparent 32%),radial-gradient(circle at 72% 120%,rgba(14,165,168,.11),transparent 38%),rgba(255,255,255,.86);box-shadow:var(--shadow-xl);backdrop-filter:blur(18px)}
    .hero:before{content:"";position:absolute;width:92px;height:7px;background:linear-gradient(90deg,var(--coral),#FF9B70);top:0;left:34px;border-radius:0 0 99px 99px}
    .hero:after{content:"";position:absolute;width:220px;height:220px;border:1px solid rgba(37,99,235,.13);border-radius:50%;right:-70px;top:-115px;box-shadow:0 0 0 34px rgba(37,99,235,.035),0 0 0 70px rgba(14,165,168,.025)}
    .hero-kicker{font-size:.64rem;letter-spacing:.18em;text-transform:uppercase;color:var(--cobalt);font-weight:800;margin:17px 0 8px}
    .hero h1{font-size:clamp(2.25rem,4vw,4.15rem);line-height:1.02;margin:.08rem 0 .7rem;max-width:1100px;background:linear-gradient(100deg,#071A33,#175C91 58%,#2563EB);-webkit-background-clip:text;background-clip:text;color:transparent!important}
    .hero p{font-size:1.02rem;line-height:1.65;margin:0;max-width:860px;color:#65758A}

    /* top strip */
    .intel-strip{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:-8px 0 22px}
    .intel-chip{border:1px solid var(--line);background:rgba(255,255,255,.92);padding:7px 11px;border-radius:999px;font-size:.7rem;color:#65758A;font-weight:700}
    .intel-chip strong{color:var(--ink)}

    /* METRICS — asymmetric editorial tiles */
    .metric-grid{display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr;gap:12px;margin:8px 0 26px}
    .metric-card{padding:21px 20px 18px;border:1px solid #DCE5EF;border-radius:18px;background:rgba(255,255,255,.94);box-shadow:0 15px 38px rgba(17,53,86,.08);min-height:138px;position:relative;overflow:hidden;transition:.22s cubic-bezier(.2,.8,.2,1)}
    .metric-card:hover{transform:translateY(-5px);box-shadow:0 23px 52px rgba(17,53,86,.14);border-color:#B7D5F2}
    .metric-card:first-child{background:linear-gradient(145deg,#071A33,#15598A);border-color:#15598A;transform:translateY(-3px)}
    .metric-card:first-child .metric-label,.metric-card:first-child .metric-note{color:#D8E3EF}.metric-card:first-child .metric-value{color:white}
    .metric-card:after{position:absolute;right:17px;bottom:8px;font:800 4.4rem 'Plus Jakarta Sans';color:#0D3F7509;line-height:1}.metric-card:nth-child(1):after{content:"01";color:#FFFFFF0A}.metric-card:nth-child(2):after{content:"02"}.metric-card:nth-child(3):after{content:"03"}.metric-card:nth-child(4):after{content:"04"}
    .metric-card:nth-child(2):before,.metric-card:nth-child(3):before,.metric-card:nth-child(4):before{content:"";position:absolute;top:0;left:0;width:100%;height:5px;background:linear-gradient(90deg,var(--electric),#5DAEFF)}
    .metric-card:nth-child(3):before{background:var(--coral)}.metric-card:nth-child(4):before{background:#7EA6C9}
    .metric-label{color:#6F7D8F;font-size:.63rem;text-transform:uppercase;letter-spacing:.13em;font-weight:800}
    .metric-value{font-family:'Plus Jakarta Sans';font-size:2.5rem;color:var(--ink);font-weight:800;margin:14px 0 3px;letter-spacing:-.05em}
    .metric-note{font-size:.71rem;color:#748399}.metric-accent{color:var(--cobalt)}

    /* containers */
    div[data-testid="stVerticalBlockBorderWrapper"]{
      border:1px solid #DCE5EF!important;border-radius:18px!important;background:rgba(255,255,255,.94)!important;box-shadow:0 15px 42px rgba(17,53,86,.075)!important;backdrop-filter:blur(14px);
    }
    [data-testid="stMetric"]{background:var(--paper-2);border:1px solid var(--line);padding:15px 17px;border-radius:5px;box-shadow:0 8px 20px rgba(25,30,45,.05)}
    [data-testid="stMetricLabel"]{color:#6F7D8F!important}[data-testid="stMetricValue"]{color:var(--ink)!important;font-family:'Plus Jakarta Sans';letter-spacing:-.04em;font-size:1.9rem}

    /* inputs and buttons */
    .stButton>button,.stDownloadButton>button{min-height:48px;border-radius:13px;border:1px solid #CBD8E6;background:linear-gradient(180deg,#FFFFFF,#F5F9FD);color:var(--ink);font-weight:750;transition:.2s cubic-bezier(.2,.8,.2,1);box-shadow:0 5px 15px rgba(13,63,117,.07);font-size:1rem}
    .stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--ink);color:var(--ink);transform:translateY(-2px);box-shadow:0 6px 0 rgba(13,63,117,.08)}
    .stButton>button[kind="primary"]{background:linear-gradient(105deg,#1858C9,#287DE7);color:white;border:0;box-shadow:0 12px 28px rgba(37,99,235,.28)}
    .stButton>button[kind="primary"]:hover{background:linear-gradient(105deg,#124DB8,#176DD5);color:white;transform:translateY(-3px);box-shadow:0 17px 34px rgba(37,99,235,.35)}
    .stTextInput input,.stTextArea textarea,[data-baseweb="select"]>div{background:rgba(255,255,255,.96)!important;border:1px solid #C8D7E6!important;color:var(--ink)!important;border-radius:12px!important;box-shadow:0 4px 14px rgba(30,72,110,.04)!important;min-height:48px}
    .stTextInput input:focus,.stTextArea textarea:focus{border-color:var(--cobalt)!important;box-shadow:0 0 0 3px rgba(23,105,176,.10)!important}
    [data-testid="stFileUploaderDropzone"]{background:radial-gradient(circle at 85% 20%,#2563EB12,transparent 32%),linear-gradient(135deg,#FBFDFF,#EFF7FD);border:2px dashed #9FB9D2;border-radius:20px;padding:32px;min-height:145px;transition:.25s ease;position:relative;overflow:hidden}
    [data-testid="stFileUploaderDropzone"]:after{content:"PDF  ·  CSV  ·  TXT";position:absolute;right:22px;bottom:13px;font-size:.62rem;letter-spacing:.16em;font-weight:800;color:#6F91AD}
    [data-testid="stFileUploaderDropzone"]:hover{border-color:var(--electric);background:linear-gradient(135deg,#FFFFFF,#E8F4FF);transform:translateY(-3px);box-shadow:0 20px 45px rgba(37,99,235,.13)}

    /* tables */
    [data-testid="stDataFrame"]{border:1px solid #D5E1EC;border-radius:15px;overflow:hidden;background:#FFFFFF;box-shadow:0 14px 36px rgba(24,58,90,.08)}
    [data-testid="stDataFrame"] *{font-family:'Inter'!important;font-size:16px!important;color:#0A2540!important}
    [data-testid="stDataFrame"] [role="columnheader"]{font-size:16px!important;font-weight:800!important;color:#082C50!important;background:#EDF5FC!important}
    [data-testid="stDataFrame"] [role="gridcell"]{font-size:16px!important;line-height:1.55!important}
    [data-testid="stDataFrame"] [role="row"]{transition:background .15s ease,transform .15s ease}
    [data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"]{background:#EAF5FF!important;color:#071A33!important}
    [data-testid="stDataFrame"] canvas{filter:saturate(1.08) contrast(1.02)}

    /* event gallery — a visual alternative to spreadsheet mode */
    .event-gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:10px 0 24px}
    .event-card{position:relative;padding:18px 18px 16px;background:linear-gradient(145deg,#FFFFFF,#F7FAFD);border:1px solid #D8E4EF;border-radius:18px;box-shadow:0 12px 32px rgba(17,53,86,.07);overflow:hidden;transition:.23s cubic-bezier(.2,.8,.2,1)}
    .event-card:before{content:"";position:absolute;inset:0 auto 0 0;width:5px;background:#D97706}.event-card.ok:before{background:#16865C}.event-card.bad:before{background:#C2413A}
    .event-card:after{content:"";position:absolute;width:110px;height:110px;border-radius:50%;right:-58px;bottom:-65px;background:#2563EB0A;box-shadow:0 0 0 24px #0EA5A806}
    .event-card:hover{transform:translateY(-7px) rotateX(1deg);border-color:#8DBDE8;box-shadow:0 25px 55px rgba(17,53,86,.15)}
    .event-top{display:flex;justify-content:space-between;gap:10px;align-items:center;font-size:.75rem;color:#4D6880;font-weight:800}.event-top i{font-style:normal;font-size:.64rem;text-transform:uppercase;letter-spacing:.08em;padding:5px 8px;border-radius:99px;background:#EAF1F7;color:#466078}.event-card.ok .event-top i{background:#E5F7EE;color:#11734F}.event-card.review .event-top i{background:#FFF4DE;color:#9A5D00}.event-card.bad .event-top i{background:#FCE9EA;color:#A52E37}
    .event-card h4{font-size:1rem!important;line-height:1.35;letter-spacing:-.02em!important;margin:17px 0 8px;min-height:2.7em}.event-number{font:800 2rem 'Plus Jakarta Sans';color:#0A3158;letter-spacing:-.05em}.event-number small{font:700 .78rem Inter;color:#6B8296;letter-spacing:0}.event-meta{display:flex;justify-content:space-between;margin-top:15px;padding-top:12px;border-top:1px solid #E2EAF2;font-size:.74rem}.event-meta b{color:#15598A}.event-meta span{color:#6D7E8F}.event-source{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:10px;color:#8493A2;font-size:.68rem}

    /* charts, controls and micro-interactions */
    [data-testid="stPlotlyChart"]{background:rgba(255,255,255,.8);border:1px solid #DCE6F0;border-radius:18px;padding:10px;box-shadow:0 16px 42px rgba(17,53,86,.07);overflow:hidden}
    [data-testid="stPlotlyChart"]:hover{box-shadow:0 22px 52px rgba(17,53,86,.12)}
    [data-baseweb="popover"]{border-radius:14px!important;box-shadow:0 24px 70px rgba(7,26,51,.2)!important}
    [data-testid="stToast"]{border-radius:14px!important;box-shadow:0 18px 50px rgba(7,26,51,.18)!important}
    [data-testid="stProgress"] > div > div{background:linear-gradient(90deg,#2563EB,#0EA5A8)!important}
    button:focus-visible,input:focus-visible,[role="option"]:focus-visible{outline:3px solid rgba(37,99,235,.28)!important;outline-offset:2px!important}

    /* tabs / segmented */
    div[data-baseweb="tab-list"]{gap:2px;background:transparent;border-bottom:1px solid var(--line);padding:0;border-radius:0}
    button[data-baseweb="tab"]{border-radius:0;color:#6F7D8F;padding:.7rem 1rem;border-bottom:3px solid transparent;font-weight:700}
    button[data-baseweb="tab"][aria-selected="true"]{background:transparent;color:var(--ink);border-bottom-color:var(--coral)}
    [data-testid="stSegmentedControl"]{background:#EDF2F7;padding:4px;border-radius:8px}

    /* expanders and messages */
    [data-testid="stExpander"]{border:1px solid var(--line)!important;background:rgba(255,255,255,.92)!important;border-radius:5px!important}
    [data-testid="stAlert"]{border-radius:6px!important;border-left-width:5px!important}
    [data-testid="stAlert"]{border:1px solid #D8E5EF!important;border-left:6px solid var(--aqua)!important;border-radius:16px!important;background:linear-gradient(105deg,#FFFFFF,#F1FAF8)!important;box-shadow:0 12px 28px rgba(17,53,86,.06)!important;padding:1rem 1.1rem!important}
    .soft-divider{height:1px;background:var(--line);margin:16px 0 20px}
    .status-ok{color:#1769B0}.status-review{color:var(--warning)}.status-bad{color:var(--danger)}
    .empty-state{padding:48px 30px;text-align:left;border:1px solid var(--line);border-radius:5px;background:var(--paper-2);box-shadow:var(--shadow);position:relative}
    .empty-state:before{content:"00";position:absolute;right:24px;top:13px;font-family:'Manrope';font-weight:800;font-size:4.6rem;color:#E7EDF4;line-height:1}
    .empty-state b{display:block;color:var(--ink);font-family:'Manrope';font-size:1.25rem;margin-bottom:8px}.empty-state span{color:#6F7D8F;max-width:600px;display:block}

    /* workspace modules */
    .workspace-intro{display:grid;grid-template-columns:1.4fr .8fr;gap:12px;margin-bottom:18px}
    .workspace-note{background:var(--cobalt-soft);border-left:5px solid var(--cobalt);padding:15px 17px;border-radius:3px;color:#315677;font-size:.82rem;line-height:1.55}
    .workspace-signal{background:var(--coral-soft);border-left:5px solid var(--coral);padding:15px 17px;border-radius:3px;color:#7F3539;font-size:.82rem;line-height:1.55}
    .section-index{display:flex;align-items:baseline;gap:12px;margin:20px 0 9px}.section-index span{font-family:'Manrope';font-size:.68rem;font-weight:800;color:var(--coral);letter-spacing:.16em}.section-index b{font-family:'Manrope';font-size:1.12rem;color:var(--ink)}
    .section-index:after{content:"";height:1px;flex:1;background:linear-gradient(90deg,#BCD0E2,transparent);margin-left:8px}

    /* AUTH — radically different from dashboard */
    .auth-page-heading{padding:10px 0 20px;border-bottom:1px solid var(--line);margin-bottom:25px}
    .auth-page-heading span{font-size:.62rem;letter-spacing:.2em;color:var(--coral);font-weight:800}.auth-page-heading h1{font-size:2.5rem;margin:.25rem 0 .35rem}.auth-page-heading p{max-width:690px;margin:0}
    .auth-brand-card{background:var(--navy);color:white;padding:38px;border-radius:5px;min-height:560px;position:relative;overflow:hidden;box-shadow:8px 8px 0 var(--coral)}
    .auth-brand-card:after{content:"";position:absolute;width:330px;height:330px;border:52px solid rgba(255,255,255,.05);border-radius:50%;right:-130px;bottom:-120px}
    .brand-topline{display:flex;gap:12px;align-items:center}.brand-mark{width:42px;height:42px;border-radius:50%;background:var(--coral);display:grid;place-items:center;font-family:'Manrope';font-weight:800}.brand-kicker{font-size:.62rem;letter-spacing:.16em;font-weight:800;color:#C5D6E8}.brand-small{font-size:.75rem;color:#AFC1D4;margin-top:2px}
    .auth-brand-card h1{font-size:3.8rem;color:white!important;max-width:430px;line-height:.95;margin:65px 0 20px}.brand-lead{color:#D5E1EC!important;font-size:1rem!important;max-width:520px;line-height:1.65}
    .auth-benefits{margin-top:45px;display:grid;gap:14px}.auth-benefits>div{display:grid;grid-template-columns:34px 1fr;gap:12px;align-items:start;border-top:1px solid rgba(255,255,255,.11);padding-top:13px}.auth-benefits span{color:#F06C73;font-family:'Manrope';font-weight:800}.auth-benefits p{margin:0;color:#D3DFEA!important;font-size:.78rem}.auth-benefits b{color:white}.brand-footer-note{position:absolute;bottom:25px;left:38px;color:#B1C2D4;font-size:.65rem;letter-spacing:.13em;text-transform:uppercase}
    .auth-title-block{margin:10px 0 24px}.secure-pill{display:inline-block;background:var(--lime);color:#17365D;padding:5px 9px;border-radius:99px;font-size:.62rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.auth-title-block h2{font-size:2rem;margin:.55rem 0 .35rem}.auth-help{margin-top:18px;padding:12px 0;border-top:1px solid var(--line);font-size:.75rem;color:#6F7D8F}.auth-bottom-note{text-align:center;color:#8390A0;font-size:.67rem;margin-top:25px;letter-spacing:.05em}

    @media(max-width:1050px){.metric-grid{grid-template-columns:repeat(2,1fr)}.event-gallery{grid-template-columns:repeat(2,1fr)}.workspace-intro{grid-template-columns:1fr}.block-container{padding:1.4rem}.auth-brand-card{min-height:420px}.auth-brand-card h1{margin-top:35px;font-size:3rem}}
    @media(max-width:680px){.metric-grid,.event-gallery{grid-template-columns:1fr}.hero h1{font-size:2.2rem}.hero{padding:27px 22px}.block-container{padding:1rem}.auth-brand-card{padding:25px}.auth-brand-card h1{font-size:2.6rem}}

    /* v4.7 validation language */
    .validation-badge,.type-badge{display:inline-flex;align-items:center;gap:7px;border:1px solid;padding:6px 10px;border-radius:999px;font-family:'DM Sans';font-size:.72rem;font-weight:800;letter-spacing:.01em}
    .validation-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
    .observation-detail{background:linear-gradient(135deg,#FFFFFF 0%,#F1F5F9 100%);border:1px solid var(--line);border-left:6px solid var(--cobalt);padding:22px 24px;border-radius:6px;box-shadow:0 12px 32px rgba(24,29,43,.06);margin:10px 0 16px}
    .detail-kicker{font-family:'Manrope';font-size:.62rem;letter-spacing:.18em;color:var(--coral);font-weight:900}.observation-detail h3{font-size:1.25rem;margin:5px 0 12px}.detail-value{font-family:'Manrope';font-weight:800;font-size:2rem;color:var(--ink)}.detail-value span{font-family:'DM Sans';font-size:.9rem;color:#6F7D8F;font-weight:700}.detail-meta{font-size:.78rem;color:#748399;margin:5px 0 14px}.detail-badges{display:flex;gap:8px;flex-wrap:wrap}
    .evidence-ok{padding:7px 10px;margin:5px 0;border-left:3px solid #16865C;background:#16865C0D;color:#315677;font-size:.78rem;border-radius:2px}.evidence-warning{padding:7px 10px;margin:5px 0;border-left:3px solid #D97706;background:#D977060D;color:#7A5410;font-size:.78rem;border-radius:2px}

    /* v4.16 — Economic Intelligence Workspace */
    .analysis-rail{display:flex;align-items:center;gap:12px;padding:13px 15px;margin:-2px 0 16px;background:#0D3F75;color:#F0F5FA;border-radius:9px;box-shadow:0 10px 30px rgba(17,24,39,.13)}
    .analysis-rail>div{display:flex;align-items:center;gap:7px;white-space:nowrap}.analysis-rail span{font-family:'Manrope';font-size:.61rem;color:#9DC4E6;border:1px solid #9DC4E655;border-radius:99px;padding:3px 6px}.analysis-rail b{font-size:.72rem}.analysis-rail i{height:1px;background:#44749F;flex:1}
    .intel-strip{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 18px}.intel-chip{border:1px solid #D7DEE8;background:#FFFFFF;padding:8px 11px;border-radius:999px;font-size:.68rem;color:#6F7D8F;text-transform:uppercase;letter-spacing:.07em;font-weight:800}.intel-chip strong{color:#17365D;margin-left:6px;font-size:.76rem}
    .brief-panel{border-top:4px solid #3157D5;background:#FFFFFF;padding:20px 21px;margin-bottom:12px;min-height:145px}.brief-panel.dark{background:#0D3F75;color:#F0F5FA;border-top-color:#9DC4E6}.brief-panel h3{font-size:1.35rem;margin:10px 0 7px}.brief-panel.dark h3{color:white!important}.brief-panel p{font-size:.82rem;max-width:690px}
    .desk-label{font-family:'Manrope';font-size:.6rem;letter-spacing:.17em;font-weight:900;color:#D71920}
    .xray-head{display:flex;align-items:baseline;gap:13px;margin:27px 0 5px;border-top:1px solid #D7DEE8;padding-top:19px}.xray-head span{font-family:'Manrope';font-size:.62rem;letter-spacing:.18em;color:#3157D5;font-weight:900}.xray-head b{font-size:1.02rem}
    .xray-spectrum{display:flex;height:13px;border-radius:999px;overflow:hidden;background:#E7EDF4;border:3px solid #FFFFFF;box-shadow:0 0 0 1px #D7DEE8}.xr-valid{background:#16865C}.xr-review{background:#D97706}.xr-reject{background:#C2413A}.xray-legend{display:flex;gap:18px;color:#748399;font-size:.69rem;margin:8px 2px 24px}
    .review-progress{display:grid;grid-template-columns:220px 1fr;align-items:center;gap:18px;background:#0D3F75;color:white;padding:14px 17px;border-radius:8px;margin:8px 0 22px}.review-progress span{display:block;font-size:.58rem;letter-spacing:.16em;color:#9DC4E6;font-weight:900}.review-progress b{font-size:.78rem}.review-bar{height:5px;background:#2F6695;border-radius:99px;overflow:hidden}.review-bar i{display:block;height:100%;background:#9DC4E6}
    .source-quote{font-family:'Manrope';font-size:1.23rem;line-height:1.55;color:#17365D;background:#F5F8FB;border-left:5px solid #D71920;padding:22px 24px;margin:8px 0 7px;border-radius:3px}
    .binding-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0 18px}.binding-grid>div{background:#FFFFFF;border:1px solid #D7DEE8;padding:12px 13px;border-radius:5px}.binding-grid .wide{grid-column:1/-1}.binding-grid span{display:block;font-size:.59rem;text-transform:uppercase;letter-spacing:.11em;color:#7D8A9B;font-weight:800;margin-bottom:5px}.binding-grid b{font-size:.82rem;color:#17365D}
    .confidence-orbit{width:132px;height:132px;border-radius:50%;border:12px solid #E7EDF4;box-shadow:inset 0 0 0 2px #3157D5;display:flex;align-items:center;justify-content:center;gap:4px;margin:8px auto 18px;background:#FFFFFF}.confidence-orbit strong{font-family:'Manrope';font-size:2.25rem;color:#17365D}.confidence-orbit span{font-size:.61rem;color:#748399;line-height:1.05;text-transform:uppercase;font-weight:800}
    @media(max-width:800px){.analysis-rail i{display:none}.analysis-rail{flex-wrap:wrap}.review-progress{grid-template-columns:1fr}.binding-grid{grid-template-columns:1fr}}

    /* v6.0 — ITCEQ institutional workspace: compact, white, analytical */
    [data-testid="stSidebar"]{background:#FFFFFF!important;border-right:1px solid #DFE6EE!important;box-shadow:8px 0 30px rgba(27,61,99,.045)!important}
    [data-testid="stSidebar"] *{color:#29445F}
    .institution-lockup{height:112px;padding:20px 17px 14px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #E6EBF1;position:relative}
    .institution-lockup:after{content:"";position:absolute;width:95px;height:95px;border:3px solid #ED1C2E;border-color:#ED1C2E transparent transparent transparent;border-radius:50%;left:-37px;top:7px;transform:rotate(-21deg)}
    .institution-lockup strong{display:block;color:#1459B8;font:800 1.15rem 'Plus Jakarta Sans';letter-spacing:.18em}.institution-lockup span{display:block;color:#74869A;font-size:.61rem;text-transform:uppercase;letter-spacing:.1em;margin-top:2px}
    .itceq-symbol{width:48px;height:54px;position:relative;border-right:9px solid #9AA3AE;border-bottom:9px solid #9AA3AE;z-index:1}.itceq-symbol:before{content:"";position:absolute;width:22px;height:22px;background:#1559B7;border-radius:50%;left:8px;top:14px;box-shadow:inset -5px -4px 0 #0B3C8A}.itceq-symbol i{position:absolute;width:28px;height:7px;background:#9AA3AE;right:-9px;top:0}.itceq-symbol b{display:none}
    .brand-lockup{padding:22px 18px 14px!important;margin:0 0 12px!important;border:0!important;gap:10px!important}.brand-lockup:after{display:none}.brand-arc{width:4px;height:46px;background:#ED1C2E;border-radius:99px;transform:rotate(13deg);box-shadow:12px -14px 0 -1px #ED1C2E}.brand-name{font-size:1.55rem!important;color:#1256AF!important}.brand-sub{color:#687B8F!important;font-size:.58rem!important;letter-spacing:.09em!important}
    .side-section{color:#8A98A8!important;font-size:.6rem!important;margin:20px 17px 8px!important}
    [data-testid="stSidebar"] .stRadio label{min-height:43px!important;padding:9px 13px!important;border-radius:7px!important;font-size:.86rem!important;color:#35506B!important}
    [data-testid="stSidebar"] .stRadio label p{font-size:.86rem!important;color:#35506B!important}
    [data-testid="stSidebar"] .stRadio label:hover{background:#F0F5FA!important;transform:none!important;color:#1358B2!important}
    [data-testid="stSidebar"] .stRadio label:has(input:checked){background:#E8F1FD!important;border-color:#D7E7FA!important;box-shadow:none!important;position:relative}
    [data-testid="stSidebar"] .stRadio label:has(input:checked):before{content:"";position:absolute;left:0;top:8px;bottom:8px;width:3px;background:#155CC4;border-radius:0 4px 4px 0}
    [data-testid="stSidebar"] .stRadio label:has(input:checked) *{color:#1358B2!important}
    .user-chip{background:#F3F6F9!important;border:1px solid #E2E8EF!important;border-radius:9px!important;margin:10px 10px!important}.user-chip b{color:#173B69!important}.user-chip span{color:#718297!important}
    [data-testid="stSidebar"] .stCaption{color:#8392A1!important}

    .stApp{background:#F7F9FC!important;color:#173B69}
    header[data-testid="stHeader"]{background:rgba(255,255,255,.95)!important;border-bottom:1px solid #E4E9EF!important;box-shadow:0 2px 12px rgba(17,53,86,.035)}
    .block-container{max-width:1550px!important;padding:1.45rem 2rem 4rem!important}
    .hero{padding:24px 30px 25px!important;margin-bottom:22px!important;border-radius:13px!important;background:#FFFFFF!important;border:1px solid #E0E7EF!important;box-shadow:0 5px 18px rgba(23,59,105,.045)!important}
    .hero:before{width:4px!important;height:46px!important;left:0!important;top:24px!important;border-radius:0 5px 5px 0!important;background:#ED1C2E!important}.hero:after{width:135px!important;height:135px!important;right:-55px!important;top:-85px!important;box-shadow:0 0 0 22px #155CC408,0 0 0 45px #155CC405!important}
    .hero-kicker{margin:0 0 8px!important;color:#155CC4!important;font-size:.59rem!important}.hero h1{font-size:clamp(2rem,3vw,3rem)!important;background:none!important;color:#102F52!important;line-height:1.04!important}.hero p{font-size:.9rem!important;max-width:930px!important;line-height:1.6!important}
    .metric-grid{grid-template-columns:repeat(4,1fr)!important;gap:10px!important}.metric-card,.metric-card:first-child{min-height:112px!important;padding:16px 17px!important;border-radius:10px!important;background:#FFFFFF!important;border:1px solid #E0E7EF!important;box-shadow:0 5px 16px rgba(23,59,105,.055)!important;transform:none!important}.metric-card:hover{transform:translateY(-3px)!important;border-color:#B9D2EF!important;box-shadow:0 10px 24px rgba(23,59,105,.10)!important}.metric-card:first-child .metric-label,.metric-card:first-child .metric-note{color:#6F7D8F!important}.metric-card:first-child .metric-value{color:#1459B8!important}.metric-value{font-size:2rem!important;margin:9px 0 1px!important;color:#1459B8!important}.metric-card:before{height:2px!important}.metric-card:after{font-size:3.2rem!important}
    div[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stPlotlyChart"]{border-radius:11px!important;background:#FFFFFF!important;border:1px solid #E0E7EF!important;box-shadow:0 5px 18px rgba(23,59,105,.05)!important;backdrop-filter:none!important}
    [data-testid="stDataFrame"]{border-radius:9px!important;border:1px solid #DDE5ED!important;box-shadow:none!important}[data-testid="stDataFrame"] [role="columnheader"]{background:#F2F6FA!important;color:#36516B!important;font-size:14px!important}[data-testid="stDataFrame"] [role="gridcell"]{font-size:14px!important}[data-testid="stDataFrame"] *{font-size:14px!important}
    .event-gallery{grid-template-columns:repeat(3,minmax(0,1fr))!important}.event-card{border-radius:10px!important;box-shadow:0 4px 14px rgba(23,59,105,.055)!important}.event-card:hover{transform:translateY(-4px)!important;box-shadow:0 10px 24px rgba(23,59,105,.11)!important}
    .stButton>button,.stDownloadButton>button{border-radius:7px!important;min-height:42px!important;box-shadow:none!important}.stButton>button[kind="primary"]{background:#125BC5!important;box-shadow:0 5px 14px #125BC526!important}.stTextInput input,.stTextArea textarea,[data-baseweb="select"]>div{border-radius:7px!important;min-height:42px!important;box-shadow:none!important}
    [data-testid="stAlert"]{border-radius:8px!important;box-shadow:none!important;background:#F1F7FD!important;border-color:#D7E7F6!important;border-left-color:#155CC4!important}
    [data-testid="stFileUploaderDropzone"]{border-radius:10px!important;min-height:112px!important;background:#F8FAFD!important;box-shadow:none!important}[data-testid="stFileUploaderDropzone"]:hover{transform:none!important;border-color:#155CC4!important;background:#F1F7FE!important;box-shadow:inset 0 0 0 1px #155CC4!important}
    @media(max-width:1050px){.metric-grid{grid-template-columns:repeat(2,1fr)!important}.event-gallery{grid-template-columns:repeat(2,1fr)!important}}
    @media(max-width:680px){.metric-grid,.event-gallery{grid-template-columns:1fr!important}.block-container{padding:1rem!important}}

    /* v6.0.1 — precise brand alignment and stronger typography */
    [data-testid="stSidebar"]>div:first-child{overflow-x:hidden!important}
    .institution-lockup{height:106px!important;padding:18px 24px 14px 35px!important;gap:15px!important;overflow:visible!important}
    .institution-lockup:after{width:82px!important;height:82px!important;left:7px!important;top:9px!important;border-width:2.5px!important;transform:rotate(-18deg)!important;pointer-events:none}
    .itceq-symbol{width:50px!important;height:52px!important;flex:0 0 50px!important;margin-left:8px!important}
    .institution-lockup strong{font-size:1.12rem!important;font-weight:900!important;letter-spacing:.16em!important;line-height:1!important}
    .institution-lockup span{font-size:.62rem!important;font-weight:700!important;letter-spacing:.095em!important;margin-top:7px!important}
    .brand-lockup{min-height:88px!important;padding:17px 24px 16px 43px!important;margin:0 12px 10px!important;border-bottom:1px solid #E6EBF1!important;align-items:center!important;gap:15px!important}
    .brand-arc{width:4px!important;height:47px!important;flex:0 0 4px!important;margin:0!important;transform:rotate(12deg)!important;box-shadow:12px -13px 0 -1px #ED1C2E!important}
    .brand-name{font-size:1.48rem!important;font-weight:900!important;line-height:1!important;letter-spacing:-.045em!important}
    .brand-sub{font-size:.57rem!important;font-weight:800!important;line-height:1.35!important;letter-spacing:.085em!important;margin-top:8px!important;white-space:nowrap!important}

    html,body,[class*="css"]{font-weight:500!important}
    p,.stCaption,[data-testid="stMarkdownContainer"] p{font-weight:500!important;color:#556E86!important}
    label,.stSelectbox label,.stTextInput label,.stTextArea label{font-weight:700!important;color:#34516E!important}
    [data-testid="stSidebar"] .stRadio label,[data-testid="stSidebar"] .stRadio label p{font-weight:700!important}
    .side-section{font-weight:900!important;color:#74869A!important}
    .hero p{font-weight:550!important;color:#567089!important}
    .metric-label{font-weight:900!important;color:#60758A!important}.metric-note{font-weight:600!important;color:#687F95!important}
    [data-testid="stDataFrame"] [role="columnheader"]{font-weight:800!important}
    [data-testid="stDataFrame"] [role="gridcell"]{font-weight:600!important;color:#294762!important}
    .stButton>button,.stDownloadButton>button{font-weight:800!important}
    button[data-baseweb="tab"]{font-weight:800!important}
    [data-baseweb="select"] input,.stTextInput input,.stTextArea textarea{font-weight:600!important}

    /* v6.1.0 — institutional authentication experience */
    .auth-page-heading{display:flex!important;align-items:center!important;gap:18px!important;padding:4px 0 18px!important;margin-bottom:28px!important;border-bottom:1px solid #DDE6EF!important}
    .auth-page-heading span{font-size:.66rem!important;letter-spacing:.18em!important;color:#ED1C2E!important;font-weight:900!important;white-space:nowrap}
    .auth-page-heading h1{font-size:1.25rem!important;margin:0!important;color:#1059B5!important;letter-spacing:-.04em!important}
    .auth-page-heading p{font-size:.78rem!important;margin:0!important;color:#6A7F93!important;font-weight:650!important}
    .auth-brand-card{min-height:590px!important;padding:35px 42px 30px!important;border-radius:18px!important;background:radial-gradient(circle at 100% 100%,#DCEBFA 0,transparent 37%),linear-gradient(145deg,#FFFFFF 0%,#F7FAFE 65%,#EDF5FC 100%)!important;color:#0A3158!important;border:1px solid #D6E1EC!important;box-shadow:0 22px 58px rgba(16,54,91,.11)!important;overflow:hidden!important}
    .auth-brand-card:before{content:"";position:absolute;left:-45px;top:-52px;width:170px;height:170px;border:2px solid #ED1C2E;border-right-color:transparent;border-bottom-color:transparent;border-radius:50%;transform:rotate(23deg)}
    .auth-brand-card:after{width:290px!important;height:290px!important;border:1px solid rgba(17,91,177,.12)!important;right:-110px!important;bottom:-115px!important;box-shadow:0 0 0 38px rgba(17,91,177,.035),0 0 0 76px rgba(17,91,177,.022)!important}
    .auth-institution-lockup{display:flex;align-items:center;gap:14px;padding:4px 0 23px;border-bottom:1px solid #DDE6EF;position:relative;z-index:2}
    .auth-itceq-symbol{width:54px;height:54px;position:relative;border-right:9px solid #8B98A8;border-bottom:9px solid #8B98A8;box-sizing:border-box}
    .auth-itceq-symbol:before{content:"";position:absolute;width:22px;height:22px;background:#1059B5;border-radius:50%;left:5px;bottom:5px}
    .auth-itceq-symbol:after{content:"";position:absolute;width:28px;height:8px;background:#8B98A8;right:-9px;top:0}
    .auth-institution-lockup strong{display:block;font:900 1.2rem 'Plus Jakarta Sans';letter-spacing:.16em;color:#1059B5}.auth-institution-lockup span{display:block;margin-top:6px;font-size:.6rem;font-weight:800;letter-spacing:.12em;color:#7C8C9D}
    .auth-econia-lockup{display:flex;align-items:center;gap:12px;margin:24px 0 28px;position:relative;z-index:2}.auth-econia-lockup i{display:block;width:4px;height:43px;background:#ED1C2E;transform:skew(-13deg);box-shadow:11px -12px 0 -1px #ED1C2E}.auth-econia-lockup strong{display:block;font:900 1.7rem 'Plus Jakarta Sans';letter-spacing:-.055em;color:#1059B5}.auth-econia-lockup span{display:block;margin-top:5px;font-size:.54rem;letter-spacing:.12em;font-weight:900;color:#61778D}
    .auth-brand-copy{position:relative;z-index:2}.auth-brand-copy .brand-kicker{font-size:.61rem!important;color:#ED1C2E!important;font-weight:900!important;letter-spacing:.16em!important}.auth-brand-card h1{font-size:2.65rem!important;line-height:1.04!important;max-width:570px!important;color:#082B50!important;margin:15px 0 17px!important;letter-spacing:-.055em!important}.auth-brand-card .brand-lead{font-size:.94rem!important;line-height:1.65!important;max-width:570px!important;color:#526D86!important;font-weight:600!important}
    .auth-benefits{position:relative;z-index:2;margin-top:27px!important;border-top:1px solid #DDE6EF!important}.auth-benefits>div{display:grid!important;grid-template-columns:48px 1fr!important;gap:8px!important;padding:13px 0!important;border-bottom:1px solid #E2E9F0!important}.auth-benefits span{font:900 .7rem 'Plus Jakarta Sans'!important;color:#ED1C2E!important;letter-spacing:.08em!important}.auth-benefits p{font-size:.75rem!important;line-height:1.45!important;margin:0!important;color:#6B7F92!important}.auth-benefits b{color:#183E64!important;font-weight:850!important}.brand-footer-note{position:relative!important;z-index:2!important;margin-top:16px!important;font-size:.58rem!important;letter-spacing:.17em!important;font-weight:900!important;color:#1059B5!important}
    .auth-title-block{padding:46px 12px 18px!important}.auth-title-block .secure-pill{background:#EAF3FD!important;color:#1059B5!important;border:1px solid #D2E3F6!important;font-size:.6rem!important;font-weight:900!important;letter-spacing:.12em!important}.auth-title-block h2{font-size:2.55rem!important;margin:18px 0 10px!important;color:#082B50!important}.auth-title-block p{font-size:.92rem!important;font-weight:600!important}
    .auth-form-card-marker+div{position:relative}.auth-form-card-marker~[data-testid="stForm"]{background:#FFFFFF!important;border:1px solid #D8E2EC!important;border-radius:16px!important;padding:24px!important;box-shadow:0 18px 48px rgba(16,54,91,.10)!important}.auth-form-card-marker~[data-testid="stForm"] .stButton>button{background:linear-gradient(100deg,#1059B5,#176ED0)!important;color:#FFFFFF!important;border:0!important;min-height:49px!important;font-weight:850!important;box-shadow:0 10px 24px rgba(16,89,181,.22)!important}.auth-form-card-marker~[data-testid="stForm"] .stButton>button:hover{transform:translateY(-2px)!important;background:linear-gradient(100deg,#0B4EA5,#105FC0)!important}.auth-help{margin:30px 12px 0!important;padding-top:18px!important;border-top:1px solid #DDE6EF!important;font-size:.76rem!important;line-height:1.6!important;color:#657B90!important}.auth-help b{color:#143C63!important}.auth-bottom-note{text-align:center!important;margin-top:26px!important;color:#8796A5!important;font-size:.62rem!important;letter-spacing:.04em!important;font-weight:700!important}
    @media(max-width:900px){.auth-page-heading{display:block!important}.auth-page-heading h1{margin-top:8px!important}.auth-page-heading p{margin-top:5px!important}.auth-brand-card{min-height:auto!important}.auth-title-block{padding-top:24px!important}}
    </style>
    ''', unsafe_allow_html=True)


def hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'''<div class="hero"><div class="hero-kicker">{html.escape(kicker)}</div><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>''',
        unsafe_allow_html=True,
    )


def metric_cards(items: list[tuple[str, str, str]]) -> None:
    cards = ''.join(
        f'<div class="metric-card"><div class="metric-label">{html.escape(str(label))}</div><div class="metric-value">{html.escape(str(value))}</div><div class="metric-note">{html.escape(str(note))}</div></div>'
        for label, value, note in items
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def intel_strip(items: list[tuple[str, str]]) -> None:
    chips = ''.join(
        f'<div class="intel-chip">{html.escape(str(label))} <strong>{html.escape(str(value))}</strong></div>'
        for label, value in items
    )
    st.markdown(f'<div class="intel-strip">{chips}</div>', unsafe_allow_html=True)


def section_index(number: str, title: str) -> None:
    number_html = f"<span>{html.escape(number)}</span>" if str(number).strip() else ""
    st.markdown(
        f'<div class="section-index">{number_html}<b>{html.escape(title)}</b></div>',
        unsafe_allow_html=True,
    )
