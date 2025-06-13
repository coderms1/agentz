#score_utils.py
def score_chart_health(data):
    score = 0
    sub_scores = {}

    liquidity = float(data.get("liquidity", 0))
    if liquidity >= 100000: sub_scores["Liquidity"] = 30
    elif liquidity >= 50000: sub_scores["Liquidity"] = 20
    elif liquidity >= 10000: sub_scores["Liquidity"] = 10
    else: sub_scores["Liquidity"] = 0
    score += sub_scores["Liquidity"]

    volume = float(data.get("volume", 0))
    if volume >= 500000: sub_scores["Volume"] = 25
    elif volume >= 100000: sub_scores["Volume"] = 15
    elif volume >= 10000: sub_scores["Volume"] = 5
    else: sub_scores["Volume"] = 0
    score += sub_scores["Volume"]

    fdv = float(data.get("fdv", 0))
    if 100000 <= fdv <= 100000000: sub_scores["FDV"] = 20
    elif fdv > 100000000: sub_scores["FDV"] = 10
    else: sub_scores["FDV"] = 5
    score += sub_scores["FDV"]

    lp_burned = data.get("lp_burned", "").lower()
    if lp_burned in ["🔥", "yes", "true", "burned"]: sub_scores["LP Status"] = 15
    else: sub_scores["LP Status"] = 0
    score += sub_scores["LP Status"]

    holders = data.get("holders", "N/A")
    try:
        holders = int(holders)
        if holders >= 1000: sub_scores["Holders"] = 10
        elif holders >= 100: sub_scores["Holders"] = 5
        else: sub_scores["Holders"] = 2
    except:
        sub_scores["Holders"] = 0
    score += sub_scores["Holders"]

    if score >= 75:
        status = "🟢 Chart Health: {}/100".format(score)
        remark = "🤖 Trench0rBot Report: Looks solid. This one’s seen a few battles and lived to tell."
    elif score >= 45:
        status = "🟡 Chart Health: {}/100".format(score)
        remark = "🤖 Trench0rBot Report: Hmm. Mid-grade. Could moon. Could malfunction."
    else:
        status = "🔴 Chart Health: {}/100".format(score)
        remark = "🤖 Trench0rBot Report: Intel suggests high risk. Proceed with backup."

    sub_report = "\n".join([f"• {k}: {v}/" + ("30" if k=="Liquidity" else "25" if k=="Volume" else "20" if k=="FDV" else "15" if k=="LP Status" else "10") for k,v in sub_scores.items()])
    final_report = f"{status}\n{sub_report}\n{remark}"

    return {"score": score, "report": final_report}
