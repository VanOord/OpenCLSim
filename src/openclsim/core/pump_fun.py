"""Collection of functions for pumps."""
import math
import warnings

import numpy as np
import pandas as pd
from intersect import intersection
from scipy import interpolate
from scipy.optimize import curve_fit  # type: ignore

# from .math_fun import polyN


def poly_pump(Q, a, b, c):
    """Return the values (Head or Power) of 2nd degree poly curve."""
    Q = np.array(Q)
    return a + b * Q + c * Q**2


def poly_fit_pump_head(Q, H, Hpars=None, OffsetFit=False, nobounds=False):
    """Return the poly fit coeff (2nd degree) on pump head.

    Remarks:
        polyfit a+b*Q+c*Q**2 with RC<0 -> -b>2c
        H <0 at Q=inf                  ->  c<0
    """
    if nobounds:
        bounds = (
            [-np.inf, -np.inf, -np.inf],
            [np.inf, np.inf, np.inf],
        )
    elif Hpars:
        if OffsetFit is True:
            # Fit only on the first parameter
            eps = 1e-9
            bounds = (
                [-np.inf, Hpars[1] - eps, Hpars[2] - eps],
                [+np.inf, Hpars[1] + eps, Hpars[2] + eps],
            )
        else:
            # Limit the first param between 50% and 150%
            bounds = (
                [Hpars[0] * 0.5, -np.inf, -np.inf],
                [Hpars[0] * 1.5, np.inf, 0],
            )
    else:
        bounds = (
            [0, -np.inf, -np.inf],
            [np.inf, np.inf, 0],
        )

    popt, pcov = curve_fit(poly_pump, Q, H, bounds=bounds)

    return popt


def poly_fit_pump_power(Q, P, Ppars=None, OffsetFit=False, nobounds=False):
    """Return the poly fit coeff (2nd degree) on pump power.

    Remarks: NOT shure if bounds are correct
    """
    if nobounds:
        bounds = (
            [-np.inf, -np.inf, -np.inf],
            [np.inf, np.inf, np.inf],
        )
    elif Ppars and OffsetFit is True:
        # Fit only on the first parameter
        eps = 1e-9
        bounds = (
            [-np.inf, Ppars[1] - eps, Ppars[2] - eps],
            [+np.inf, Ppars[1] + eps, Ppars[2] + eps],
        )
    else:
        bounds = (
            [0, -np.inf, -np.inf],
            [np.inf, np.inf, 0],
        )

    popt, pcov = curve_fit(poly_pump, Q, P, bounds=bounds)
    return popt


# def calc_pump_BEP(Hpars, Ppars):
#     """Calculate the best efficiency point parameters."""
#     # Calc Q max
#     qmax = calc_pump_Qmax(Hpars)

#     # Calc BEP
#     Q = np.arange(0, np.ceil(qmax), 0.1)
#     Q[0] = 1e-10
#     H = polyN(Q, Hpars)
#     P = polyN(Q, Ppars)
#     eff = H * Q / P
#     idx = eff == max(eff)

#     # return BEP
#     return {
#         "Q": np.mean(Q[idx]),
#         "H": np.mean(H[idx]),
#         "P": np.mean(P[idx]),
#         "eff": np.mean(eff[idx]),
#     }


def calc_pump_Qmax(Hpars):
    """Calculate the flow at head = zero."""
    # Calc Q max
    a = Hpars[2]
    b = Hpars[1]
    c = Hpars[0]
    q_p = (-b + (b**2 - 4 * a * c) ** 0.5) / (2 * a)
    q_m = (-b - (b**2 - 4 * a * c) ** 0.5) / (2 * a)
    if np.iscomplex(q_p):
        q_p = 0
    if np.iscomplex(q_m):
        q_m = 0
    # return qmax
    return max(q_p, q_m)


def roundup(x, nearest_value):
    return int(math.ceil(x / nearest_value)) * nearest_value


def rounddown(x, nearest_value):
    return int(math.floor(x / nearest_value)) * nearest_value


def pump_input_check(pump_input):
    if "diam_act" not in pump_input:
        pump_input["diam_act"] = pump_input["diam_nom"]

    if "pipeFrictionModel" not in pump_input:
        pump_input["pipeFrictionModel"] = 4

    n_max = roundup(
        (
            (pump_input["power_nom"] * pump_input["rpm_nom"] ** 3)
            / pump_input["CnstP"][0]
        )
        ** (1 / 3),
        10,
    )

    if "rpm_act" not in pump_input:
        pump_input["rpm_act"] = pump_input["rpm_nom"]

    if pump_input["rpm_act"] > n_max:
        pump_input["rpm_act"] = 0.9 * n_max

    if pump_input["rpm_act"] == pump_input["rpm_nom"]:
        pump_input["rpm_act"] = pump_input["rpm_act"] - 0.01

    if "trq_lim" not in pump_input:
        pump_input["trq_lim"] = 0

    if "rpm_min" in pump_input and pump_input["rpm_min"] == pump_input["rpm_nom"]:
        pump_input["rpm_min"] = pump_input["rpm_nom"] - 0.02

    return pump_input


def pump_setpoint_check(d):
    # Check some setpoint input values
    if d["power_nom"] < 1:
        d["power_nom"] = np.nan
    if d["trq_lim"] <= 0 or d["trq_lim"] >= 1:
        d["trq_lim"] = np.nan
    if d["rpm_nom"] < 1:
        d["rpm_nom"] = 0
    if d["rpm_min"] <= 0:
        d["rpm_min"] = d["rpm_nom"]
    if d["rpm_max"] <= 0:
        d["rpm_max"] = d["rpm_nom"]
    if d["gear"] > 0:
        d["rpm_median"] = d["rpm_nom"]
    if d["rpm_median"] <= 0:
        d["rpm_median"] = d["rpm_nom"]
    if d["gear"] <= 0:
        d["rpm_min"] = roundup(0.7 * d["rpm_nom"], 10)

    # Calculate the max torque with relative torque limit
    if np.isnan(d["trq_lim"]):
        d["trq_max"] = (30 * d["power_nom"]) / (d["rpm_nom"] * math.pi)
    else:
        d["trq_max"] = (
            (30 * d["power_nom"]) / (d["rpm_nom"] * math.pi) * (1 + d["trq_lim"])
        )
    return d


def f_dens(density):
    return density / 1


def create_sg_mix(sg_mix, sg_water):
    if sg_water != 1.000:
        sg_mix = np.append(sg_mix, [1, sg_water])
    else:
        sg_mix = np.append(sg_mix, [sg_water])
    sg_mix = np.sort(sg_mix)
    return sg_mix


def calc_concentration(sg_mix, sg_water, sg_grain):
    # calculate concentration
    conc = (sg_mix - sg_water) / (sg_grain - sg_water)
    if np.size(conc) != 1:
        conc[conc > 1] = 1
        conc[conc < 0] = 0
    elif conc > 1:
        conc = 1
    elif conc < 0:
        conc = 0
    return conc


def calc_pipeFrictionModel(pump_input, soil):
    sg_mix = soil["sg_mix"]
    sg_water = soil["sg_water"]
    sg_grain = soil["sg_grain"]
    dmf = soil["dmf"]
    conc = calc_concentration(sg_mix, sg_water, sg_grain)

    if pump_input["pipeFrictionModel"] == 1:  # Homogeen Mix
        fc = sg_mix

    elif pump_input["pipeFrictionModel"] == 2:  # VOUB Stefanoff Formule
        fc = (1 - conc * (0.8 + 0.6 * math.log10(dmf / 1000))) * sg_mix

    elif pump_input["pipeFrictionModel"] == 3:  # PDL 2014 course Formule
        fc = (1 - conc * (0.78 + 0.62 * math.log10(dmf / 1000))) * sg_mix

    elif pump_input["pipeFrictionModel"] == 4:  # PROCUR
        mix = sg_mix
        mix[mix > 1.3] = 1.3
        cv = calc_concentration(mix, sg_water, sg_grain)
        fc = (1 - cv * (0.78 + 0.62 * math.log10(dmf / 1000))) * sg_mix

    if np.size(fc) != 1:
        fc[fc < 0] = 0
    elif fc < 0:
        fc = 0
    return fc


def calc_rpmMin(rpm_nom, CnstRelRpm, CnstRelTrq):
    for n, _ in enumerate(CnstRelRpm):
        if CnstRelRpm[n] > 0 and CnstRelTrq[n] >= 0:
            rpmMin = CnstRelRpm[n] * rpm_nom
            return rpmMin
        else:
            rpmMin = 0
    return rpmMin


def pumpAffinity(rpm_act, rpm_nom, diam_act, diam_nom, CnstH, CnstP):
    # calculate scaled pumpcoefficients (from affinity laws)
    # rpm ratio
    nr = rpm_act / rpm_nom

    # diameter ratio
    Dr = diam_act / diam_nom

    if 0.9571 <= Dr < 0.9654:
        Cp = 0.0265 + 1.0084 * Dr
        Ceta = 1
    elif Dr < 0.9571:
        Cp = 0.0265 + 1.0084 * Dr
        Ceta = 0.1538 + 0.8841 * Dr
    else:
        Cp = 1
        Ceta = 1

    nr2 = nr**2
    nr3 = nr**3
    Dr2 = Dr**2
    Dr4 = Dr**4

    CnstHn = [0, 0, 0]
    CnstPn = [0, 0, 0]

    # pump coefficients
    CnstHn[0] = CnstH[0] * nr2 * Dr2 * Cp
    CnstHn[1] = CnstH[1] * nr * Cp
    CnstHn[2] = CnstH[2] / Dr2 * Cp

    # power coefficients
    CnstPn[0] = CnstP[0] * nr3 * Dr4 * (Cp / Ceta)
    CnstPn[1] = CnstP[1] * nr2 * Dr2 * (Cp / Ceta)
    CnstPn[2] = CnstP[2] * nr * (Cp / Ceta)

    return CnstHn, CnstPn


def calc_constantTorque(Q, Pnom, Hpump, Ppump, eta, rpm):
    Q_CT = Q * np.sqrt(Pnom / Ppump)
    Hpump_CT = Hpump * (Pnom / Ppump)
    rpm_CT = rpm * np.sqrt(Pnom / Ppump)

    Hpump_CT[Hpump_CT < 0.01] = np.nan

    Ppump_CT = (Q_CT * Hpump_CT) / eta
    return pd.DataFrame(
        np.transpose(np.array([Q_CT, Hpump_CT, Ppump_CT, eta, rpm_CT])),
        columns=["Q", "H", "P", "eta", "n"],
    )


def calc_constantPower(Q, Pnom, Hpump, Ppump, eta, rpm):
    Q_CP = Q * (Pnom / Ppump) ** (1 / 3)
    Hpump_CP = Hpump * (Pnom / Ppump) ** (2 / 3)
    rpm_CP = rpm * (Pnom / Ppump) ** (1 / 3)

    Hpump_CP[Hpump_CP < 0.01] = np.nan

    Ppump_CP = (Q_CP * Hpump_CP) / eta
    return pd.DataFrame(
        np.transpose(np.array([Q_CP, Hpump_CP, Ppump_CP, eta, rpm_CP])),
        columns=["Q", "H", "P", "eta", "n"],
    )


def pumpCurve(Q, CnstHa, CnstPa, rpm):
    # function to calculate the pump manometric pressure
    Hpump = CnstHa[0] + CnstHa[1] * Q + CnstHa[2] * Q**2
    Ppump = CnstPa[0] + CnstPa[1] * Q + CnstPa[2] * Q**2

    Hpump[Hpump < 1] = np.nan
    Ppump[~(Hpump >= 1)] = np.nan

    eta = (Q * Hpump) / Ppump

    df = pd.DataFrame(
        np.transpose(np.array([Q, Hpump, Ppump, eta])), columns=["Q", "H", "P", "eta"]
    )
    df["n"] = rpm
    return df


def calc_Hpump(Q, CnstH):
    # function to calculate the pump manometric pressure
    return CnstH[0] + CnstH[1] * Q + CnstH[2] * Q**2


def calc_Ppump(Q, CnstP):
    # function to calculate the pump power
    return CnstP[0] + CnstP[1] * Q + CnstP[2] * Q**2


def Trq_drive(power_max, rpm_nom, rpm_act, CnstRelRpm, CnstRelTrq):
    # function to determine Drive Charateristic
    # calculate max Drive torque
    MaxT = power_max / (rpm_nom * 2 * math.pi / 60)

    # calculate relative Drive speed
    rel_rpm = rpm_act / rpm_nom

    # Interpolates the data of the Drive Characteristics
    if rel_rpm > 0:
        f_nT = interpolate.interp1d(
            CnstRelRpm, CnstRelTrq, bounds_error=False, fill_value=np.nan
        )
        relT = f_nT(rel_rpm)
        return relT * MaxT
    else:
        return 0


def calc_pumpcurve_micture(Q, n, fc, sg_mix):
    n_mix = pd.DataFrame(Q, columns=["Q"])

    n_mix["H"] = fc / 1.000 * n["H"]
    n_mix["P"] = sg_mix / 1.000 * n["P"]
    n_mix["eta"] = (Q * n_mix["H"]) / n_mix["P"]
    n_mix["n"] = n["n"]

    return n_mix


def calc_characteristic_engine(pump_input):
    df = pd.DataFrame(
        np.transpose(np.array([pump_input["CnstRelRpm"], pump_input["CnstRelTrq"]])),
        columns=["CnstRelRpm", "CnstRelTrq"],
    )
    df["n"] = df["CnstRelRpm"] * pump_input["rpm_nom"]
    df["trq"] = (
        (30 * pump_input["power_nom"]) / (pump_input["rpm_nom"] * math.pi)
    ) * df["CnstRelTrq"]
    df["P"] = df["n"] * df["trq"] * math.pi / 30
    return df


def calc_additional_pumpinfo(df, n0, width_imp, diam_act):
    bep = n0.loc[n0["eta"] == n0["eta"].max()].reset_index(drop=True)

    df["Ph"] = df["Q"] * df["H"]
    df["trq"] = (30 * df["P"]) / (df["n"] * math.pi)
    df["Qbep"] = df["n"] / bep["n"].values * bep["Q"].values
    df["QQbep"] = df["Q"] / df["Qbep"]
    df["Frad"] = 0.36 * (1 - df["QQbep"] ** 2) * df["H"] * width_imp * diam_act
    df["vtip"] = df["n"] * math.pi / 60 * diam_act
    return df


def calc_combined_pumpcurve(Q, pump_input, CnstHn, CnstPn, CnstHn0, CnstPn0):
    DriveType = pump_input["DriveType"]
    Pnom = pump_input["power_nom"]
    rpm_act = pump_input["rpm_act"]
    rpm_nom = pump_input["rpm_nom"]
    diam_act = pump_input["diam_act"]
    width_imp = pump_input["width_imp"]

    n0 = pumpCurve(Q, CnstHn0, CnstPn0, rpm_nom)
    n = pumpCurve(Q, CnstHn, CnstPn, rpm_act)

    if DriveType == "CT":
        n_CT = calc_constantTorque(
            n["Q"].values, Pnom, n["H"].values, n["P"].values, n["eta"].values, rpm_act
        )

        x, _ = intersection(n["Q"], n["H"], n_CT["Q"], n_CT["H"])

        df = (
            pd.concat(
                [
                    n.loc[n["Q"] <= x[0]],
                    n_CT.loc[n_CT["Q"] >= x[0]],
                ],
                ignore_index=True,
            )
            if x
            else n
        )

    elif DriveType == "CP":
        n_CP = calc_constantPower(
            n["Q"].values, Pnom, n["H"].values, n["P"].values, n["eta"].values, rpm_act
        )

        x, _ = intersection(n["Q"], n["H"], n_CP["Q"], n_CP["H"])

        df = (
            pd.concat(
                [
                    n.loc[n["Q"] <= x[0]],
                    n_CP.loc[n_CP["Q"] >= x[0]],
                ],
                ignore_index=True,
            )
            if x
            else n
        )

    elif DriveType == "CP-CT":
        n_CP = calc_constantPower(
            n["Q"].values, Pnom, n["H"].values, n["P"].values, n["eta"].values, rpm_act
        )
        n0_CT = calc_constantTorque(
            n0["Q"].values,
            Pnom,
            n0["H"].values,
            n0["P"].values,
            n0["eta"].values,
            rpm_nom,
        )

        xp, _ = intersection(n["Q"], n["H"], n_CP["Q"], n_CP["H"])
        xt, _ = intersection(n_CP["Q"], n_CP["H"], n0_CT["Q"], n0_CT["H"])

        if xp and xt:
            df = pd.concat(
                [
                    n.loc[n["Q"] <= xp[0]],
                    n_CP.loc[(n_CP["Q"] >= xp[0]) & (n_CP["Q"] <= xt[0])],
                    n0_CT.loc[n0_CT["Q"] >= xt[0]],
                ],
                ignore_index=True,
            )
        elif xp.any():
            df = pd.concat(
                [
                    n.loc[n["Q"] <= xp[0]],
                    n_CP.loc[n_CP["Q"] >= xp[0]],
                ],
                ignore_index=True,
            )
        elif xt.any():
            df = pd.concat(
                [
                    n.loc[n["Q"] <= xp[0]],
                    n0_CT.loc[n0_CT["Q"] >= xt[0]],
                ],
                ignore_index=True,
            )
        else:
            df = n

    elif DriveType == "CN":
        df = n.loc[n["P"] <= Pnom]

    df = calc_additional_pumpinfo(df, n0, width_imp, diam_act)
    return df


def calc_combined_pumpcurve_mixture(
    Q,
    pump_input,
    fc,
    sg_mix,
    CnstHn,
    CnstPn,
    CnstHn0,
    CnstPn0,
):
    DriveType = pump_input["DriveType"]
    Pnom = pump_input["power_nom"]
    rpm_act = pump_input["rpm_act"]
    rpm_nom = pump_input["rpm_nom"]
    diam_act = pump_input["diam_act"]
    width_imp = pump_input["width_imp"]

    n0 = pumpCurve(Q, CnstHn0, CnstPn0, rpm_nom)
    n = pumpCurve(Q, CnstHn, CnstPn, rpm_act)

    n_mix = calc_pumpcurve_micture(Q, n, fc, sg_mix)
    n0_mix = calc_pumpcurve_micture(Q, n0, fc, sg_mix)

    n_mix_CP = calc_constantPower(
        n_mix["Q"].values,
        Pnom,
        n_mix["H"].values,
        n_mix["P"].values,
        n_mix["eta"].values,
        rpm_act,
    )
    n0_mix_CT = calc_constantTorque(
        n0_mix["Q"].values,
        Pnom,
        n0_mix["H"].values,
        n0_mix["P"].values,
        n0_mix["eta"].values,
        rpm_nom,
    )
    n_mix_CT = calc_constantTorque(
        n_mix["Q"].values,
        Pnom,
        n_mix["H"].values,
        n_mix["P"].values,
        n_mix["eta"].values,
        rpm_nom,
    )

    if DriveType == "CN":
        df = n_mix.loc[n_mix["P"] <= Pnom]

    elif DriveType == "CP":
        x, _ = intersection(n_mix["Q"], n_mix["H"], n_mix_CP["Q"], n_mix_CP["H"])

        df = (
            pd.concat(
                [n_mix.loc[n["Q"] <= x[0]], n_mix_CP.loc[n_mix_CP["Q"] >= x[0]]],
                ignore_index=True,
            )
            if x
            else n_mix
        )

    elif DriveType == "CP-CT":
        xp, _ = intersection(n_mix["Q"], n_mix["H"], n_mix_CP["Q"], n_mix_CP["H"])
        xt, _ = intersection(
            n_mix_CP["Q"], n_mix_CP["H"], n0_mix_CT["Q"], n0_mix_CT["H"]
        )

        if xp and xt:
            df = pd.concat(
                [
                    n_mix.loc[n_mix["Q"] <= xp[0]],
                    n_mix_CP.loc[(n_mix_CP["Q"] >= xp[0]) & (n_mix_CP["Q"] <= xt[0])],
                    n0_mix_CT.loc[n0_mix_CT["Q"] >= xt[0]],
                ],
                ignore_index=True,
            )
        elif xp.any():
            df = pd.concat(
                [
                    n_mix.loc[n_mix["Q"] <= xp[0]],
                    n_mix_CP.loc[n_mix_CP["Q"] >= xp[0]],
                ],
                ignore_index=True,
            )
        elif xt.any():
            df = pd.concat(
                [
                    n_mix.loc[n_mix["Q"] <= xt[0]],
                    n0_mix_CT.loc[n0_mix_CT["Q"] >= xt[0]],
                ],
                ignore_index=True,
            )
        else:
            df = n_mix

    elif DriveType == "CT":
        x, _ = intersection(n_mix["Q"], n_mix["H"], n_mix_CT["Q"], n_mix_CT["H"])
        df = (
            pd.concat(
                [n_mix.loc[n["Q"] <= x[0]], n_mix_CT.loc[n_mix_CT["Q"] >= x[0]]],
                ignore_index=True,
            )
            if x
            else n_mix
        )

    df = calc_additional_pumpinfo(df, n0, width_imp, diam_act)
    return df


def calc_additional_revolutions(Q, pump, pump_input):
    rpm_nom = pump_input["rpm_nom"]
    diam_act = pump_input["diam_act"]
    diam_nom = pump_input["diam_nom"]
    CnstH = pump_input["CnstH"]
    CnstP = pump_input["CnstP"]

    nmin = np.min(
        [roundup(0.7 * pump_input["rpm_act"], 25), roundup(pump["n"].min(), 25)]
    )

    rpm_act_range = np.arange(nmin, rounddown(pump["n"].max(), 25), 25)

    df = pd.DataFrame(Q, columns=["Q"])

    for rev in rpm_act_range:
        label = f"H_rpm_{int(rev)}"
        CnstH_range, _ = pumpAffinity(rev, rpm_nom, diam_act, diam_nom, CnstH, CnstP)
        df[label] = calc_Hpump(Q, CnstH_range)

        xp, _ = intersection(pump["Q"], pump["H"], df["Q"], df[label])

        if np.size(xp) > 0:
            df[label].loc[df["Q"] > xp[0]] = np.nan

        df[label][df[label] < 25] = np.nan

    return df


def calc_PumpCurves(d):
    Q = np.arange(0, roundup(calc_pump_Qmax([d["f1"], d["f2"], d["f3"]]), 0.005), 0.005)

    rpm_min = max(0, d["rpm_min"])
    rpm_start = 100 if rpm_min == 0 else np.ceil(rpm_min / 50) * 50
    rpm = np.unique(
        np.append(
            np.arange(rpm_start, d["rpm_max"], 25),
            [d["rpm_median"], d["rpm_max"], d["rpm_nom"]],
        )
    )

    if d["gear"] > 0:
        rpm = rpm * d["gear"]

    H_line = []
    P_line = []
    T_line = []

    Q_pmax = []
    H_pmax = []
    Q_tmax = []
    H_tmax = []

    for n in rpm:
        CnstH, CnstP = pumpAffinity(
            n,
            d["rpm_nom"],
            1,
            1,
            [d["f1"], d["f2"], d["f3"]],
            [d["p1"], d["p2"], d["p3"]],
        )

        H = calc_Hpump(Q, CnstH)
        P = calc_Ppump(Q, CnstP)
        T = (30 * P) / (n * math.pi)

        H_line.append(H)
        P_line.append(P)
        T_line.append(T)

        f_PQ = interpolate.interp1d(P, Q, bounds_error=False, fill_value=np.nan)
        QP = f_PQ(d["power_nom"])

        f_QH = interpolate.interp1d(Q, H, bounds_error=False, fill_value=np.nan)
        HP = f_QH(QP)

        f_TQ = interpolate.interp1d(T, Q, bounds_error=False, fill_value=np.nan)
        QT = f_TQ(d["trq_max"])

        f_QH = interpolate.interp1d(Q, H, bounds_error=False, fill_value=np.nan)
        HT = f_QH(QT)

        Q_pmax.append(QP)
        H_pmax.append(HP)
        Q_tmax.append(QT)
        H_tmax.append(HT)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        Q_PT = np.nanmin([Q_pmax, Q_tmax], 0)

    Q_full = np.unique(np.append(Q, Q_PT))

    H_full = []
    P_full = []
    T_full = []
    H_PT = []
    P_PT = []

    for jj, n in enumerate(rpm):
        f_QH = interpolate.interp1d(
            Q, H_line[jj], bounds_error=False, fill_value=np.nan
        )
        HF = f_QH(Q_full)

        f_QP = interpolate.interp1d(
            Q, P_line[jj], bounds_error=False, fill_value=np.nan
        )
        PF = f_QP(Q_full)
        TF = (30 * PF) / (n * math.pi)

        HF = np.where(
            (PF > d["power_nom"]) | (TF > d["trq_max"]) | (HF < 25), np.nan, HF
        )
        PF = np.where(
            (PF > d["power_nom"]) | (TF > d["trq_max"]) | (HF < 25), np.nan, PF
        )
        TF = np.where(
            (PF > d["power_nom"]) | (TF > d["trq_max"]) | (HF < 25), np.nan, TF
        )

        H_full.append(HF)
        P_full.append(PF)
        T_full.append(TF)

        H_PT.append(np.interp(Q_PT[jj], Q, H_line[jj]))
        P_PT.append(np.interp(Q_PT[jj], Q, P_line[jj]))

    for jj, n in enumerate(rpm):
        if np.isnan(H_full[jj][0]):
            H_PT[jj] = np.nan

        if H_PT[jj] < 25:
            H_PT[jj] = np.nan

        if P_PT[jj] > d["power_nom"]:
            P_PT[jj] = np.nan

    return {
        "rpm": rpm,
        "Q_full": Q_full,
        "H_full": H_full,
        "P_full": P_full,
        "Q_PT": Q_PT,
        "H_PT": H_PT,
        "P_PT": P_PT,
    }


def rpm_calc(Q, pump_input, density):
    Tmax = Trq_drive(
        pump_input["power_nom"],
        pump_input["rpm_nom"],
        pump_input["rpm_act"],
        pump_input["CnstRelRpm"],
        pump_input["CnstRelTrq"],
    )

    _, CnstPn = pumpAffinity(
        pump_input["rpm_act"],
        pump_input["rpm_nom"],
        pump_input["diam_act"],
        pump_input["diam_nom"],
        pump_input["CnstH"],
        pump_input["CnstP"],
    )

    Pact = calc_Ppump(Q, CnstPn) * f_dens(density)
    Tact = (30 * Pact) / (pump_input["rpm_act"] * math.pi)

    if Tact <= Tmax:
        rpm_calc = pump_input["rpm_act"]
    else:
        rpm = pump_input["rpm_act"]
        rpm_nom = pump_input["rpm_nom"]

        d_rpm = 1
        while np.abs(d_rpm) > 0.5:
            if rpm < 0:
                rpm = 0.1
            # calculate new situation
            Tmax = Trq_drive(
                pump_input["power_nom"],
                rpm_nom,
                rpm,
                pump_input["CnstRelRpm"],
                pump_input["CnstRelTrq"],
            )

            if Tmax <= 0:
                Tmax = 0.1

            # recalc Affinity
            _, CnstPn = pumpAffinity(
                rpm,
                rpm_nom,
                pump_input["diam_act"],
                pump_input["diam_nom"],
                pump_input["CnstH"],
                pump_input["CnstP"],
            )
            # calculate Power
            Pact = calc_Ppump(Q, CnstPn) * f_dens(density)
            # calculate Torque
            Tact = (30 * Pact) / (rpm * math.pi)
            # Test and set new loop values based on: Standard TriSection Method
            if Tact <= Tmax:
                rpm_new = rpm + (np.abs(Tact - Tmax) / Tmax * rpm_nom) / 2
            else:
                rpm_new = rpm - (np.abs(Tact - Tmax) / Tmax * rpm_nom) / 2
            # set Drive speed error / diviation
            d_rpm = rpm - rpm_new
            rpm = rpm_new

        rpm_calc = rpm_new

    rpm_calc = max(rpm_calc, 1)
    return rpm_calc


def calc_pump_PDL_spinner(Qrange, pump_input, soil, density, additional_info=True):
    H = []
    P = []
    eta = []
    n = []

    for Q in Qrange:
        rpm_act = rpm_calc(Q, pump_input, density)

        CnstHa, CnstPa = pumpAffinity(
            rpm_act,
            pump_input["rpm_nom"],
            pump_input["diam_act"],
            pump_input["diam_nom"],
            pump_input["CnstH"],
            pump_input["CnstP"],
        )

        id_fc = soil["sg_mix"] == density

        H_man = calc_Hpump(Q, CnstHa) * soil["fc"][id_fc]

        if H_man[0] < 1:
            H_man = np.nan
            Power = np.nan
        else:
            H_man = H_man[0]
            Power = calc_Ppump(Q, CnstPa) * f_dens(density)

        eff = (H_man * Q) / Power if Power > 0 else np.nan

        H.append(H_man)
        P.append(Power)
        eta.append(eff)
        n.append(rpm_act)

    df = pd.DataFrame(
        np.transpose(np.array([Qrange, H, P, eta, n])),
        columns=["Q", "H", "P", "eta", "n"],
    )

    df = df.loc[df["H"] > 25]

    if additional_info:
        n0 = pumpCurve(
            Qrange, pump_input["CnstH"], pump_input["CnstP"], pump_input["rpm_nom"]
        )
        df = calc_additional_pumpinfo(
            df, n0, pump_input["width_imp"], pump_input["diam_act"]
        )
    return df


def calc_pipeline_resistance_water(
    Q,
    resistance_input,
    general,
    sg_water,
):
    d_pipe = resistance_input["d_pipe"]
    pipelinelength = resistance_input["pipelinelength"]
    LambdaModel = resistance_input["LambdaModel"]
    ksi = resistance_input["ksi"]
    heightreclamation = resistance_input["heightreclamation"]
    Z = resistance_input["Z"]
    hpump = resistance_input["hpump"]

    g = general["g"]
    if LambdaModel == 1:
        Lambda = 0.0388 * ((d_pipe * 1000) ** -0.1894)
    elif LambdaModel == 2:
        Lambda = (
            0.0137 * ((4 * Q) / (math.pi * d_pipe**2)) ** -0.15 * d_pipe**-0.25
        )  # VOHOP / VOCUT

    pipeline = (
        Lambda
        * (pipelinelength / d_pipe)
        * 0.5
        * sg_water
        * ((4 * Q) / (math.pi * d_pipe**2)) ** 2
    )
    additional = (
        ksi["additional"] * 0.5 * sg_water * ((4 * Q) / (math.pi * d_pipe**2)) ** 2
    )
    static = (heightreclamation + hpump) * g * sg_water

    ksi_suction = ksi["water"]
    vacuum = (
        (Z - hpump) * g + ksi_suction * 0.5 * ((4 * Q) / (math.pi * d_pipe**2)) ** 2
    ) * sg_water - Z * g * sg_water

    total = pipeline + additional + vacuum + static

    return pd.DataFrame(np.transpose(np.array([Q, total])), columns=["Q", "DP"])


def calc_pipeline_resistance_mixture(
    Q,
    resistance_input,
    general,
    soil,
    sg_mix,
):
    g = general["g"]
    dmf = soil["dmf"]
    sg_water = soil["sg_water"]
    sg_grain = soil["sg_grain"]
    sg_lump = soil["sg_lump"]
    d_pipe = resistance_input["d_pipe"]
    pipelinelength = resistance_input["pipelinelength"]
    LambdaModel = resistance_input["LambdaModel"]
    ksi = resistance_input["ksi"]
    heightreclamation = resistance_input["heightreclamation"]
    Z = resistance_input["Z"]
    hpump = resistance_input["hpump"]

    v = (4 * Q) / (math.pi * d_pipe**2)

    if LambdaModel == 1:
        Lambda = 0.0388 * ((d_pipe * 1000) ** -0.1894)
    elif LambdaModel == 2:
        Lambda = 0.0137 * v**-0.15 * d_pipe**-0.25  # VOHOP / VOCUT

    skt = 0.0000001 * dmf**2 + 0.0014 * dmf - 0.1365
    conc = (sg_mix - sg_water) / (sg_grain - sg_water)

    pipeline_w = 0.5 * Lambda * (pipelinelength / d_pipe) * sg_water * v**2

    if dmf < 60:
        pipeline = sg_mix / sg_water * pipeline_w

    elif 60 <= dmf < 2200:
        grain = conc * pipelinelength * g * sg_water * skt / v
        pipeline = pipeline_w + grain

    else:
        rock = (
            ((((sg_lump - sg_water) / (sg_grain - sg_water)) ** (3 / 2) * 2.1) / v)
            * conc
            * pipelinelength
            * g
            * sg_water
        )
        pipeline = pipeline_w + rock

    additional = ksi["additional"] * 0.5 * sg_mix * v**2
    static = (heightreclamation + hpump) * g * sg_mix

    ksi_suction = ksi["water"] + ksi["mixture"]

    vacuum = ((Z - hpump) * g + ksi_suction * 0.5 * v**2) * sg_mix - Z * g * sg_water

    total = pipeline + additional + vacuum + static

    return pd.DataFrame(np.transpose(np.array([Q, total])), columns=["Q", "DP"])


def calc_workingpoints(pump, pipeline_resistance):
    xw, _ = intersection(
        pump["Q"], pump["H"], pipeline_resistance["Q"], pipeline_resistance["DP"]
    )
    if xw.any():
        df = pump.iloc[(pump["Q"] - xw[-1]).abs().argsort()[:1]].reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=pump.columns)
        for column in df:
            df[column] = [np.nan]
    return df


def calc_pump_characteristics(pump_input):
    if "rpm_min" not in pump_input:
        y0 = 0.5
    else:
        y0 = pump_input["rpm_min"] / pump_input["rpm_nom"]

    if pump_input["rpm_max"] <= 0:
        pump_input["rpm_max"] = pump_input["rpm_nom"]

    if pump_input["trq_lim"] <= 0 or pump_input["trq_lim"] >= 1:
        pump_input["trq_lim"] = 0

    if pump_input["rpm_nom"] == 0:
        pump_input["rpm_nom"] = pump_input["rpm_max"]

    trq_nom = (30 * pump_input["power_nom"]) / (pump_input["rpm_nom"] * math.pi)
    trq_max = trq_nom * (1 + pump_input["trq_lim"])

    xx = np.linspace(0.6, 1.4, (140 - 60) + 1)
    yy = (
        (30 * pump_input["power_nom"])
        / (xx * pump_input["rpm_nom"] * math.pi)
        / trq_nom
    )

    if 0 < y0 < 1:
        x1 = [
            1,
            1
            if pump_input["trq_lim"] == 0
            else 1 + math.atan(trq_max / trq_nom - 1) * (1 - y0),
        ]
        y1 = [1, y0]
    else:
        x1 = [1, trq_max / trq_nom]
        y1 = [1, 0]

    x2 = [0, 1]
    y2 = [
        pump_input["rpm_max"] / pump_input["rpm_nom"],
        pump_input["rpm_max"] / pump_input["rpm_nom"],
    ]

    if pump_input["rpm_max"] > pump_input["rpm_nom"]:
        x_2, y_2 = intersection(x2, y2, xx, yy)

        xx = np.sort(np.append(xx, x_2))
        yy = np.flip(np.sort(np.append(yy, y_2)))

        x2 = [0, x_2[-1]]

        xx0 = xx[xx <= 1]
        xx0 = xx0[xx0 >= x2[1]]

        yy0 = yy[yy <= y2[1]]
        yy0 = yy0[yy0 >= 1]
    else:
        x2 = [0, 1]
        xx0 = 1
        yy0 = 1

    trq = np.array(0)
    trq = np.append(trq, xx0)
    trq = np.append(trq, x1[1])
    trq = np.append(trq, 0)

    rpm = np.array(y2[0])
    rpm = np.append(rpm, yy0)
    rpm = np.append(rpm, y1[1])
    rpm = np.append(rpm, y0)

    return np.flip(trq), np.flip(rpm)


def bindata(xdata, ydata, bins, delta=0):
    xc = bins + np.diff(np.hstack((bins, 0))) / 2
    xc = xc[:-1]

    digitized = np.digitize(xdata, bins)
    bin_count = np.array(
        [digitized[digitized == jj].sum() / jj for jj in range(1, len(bins))]
    )

    if 0 < delta < 0.5:
        idxs = bin_count > np.round(bin_count.sum() * delta)
    else:
        idxs = bin_count > 0

    bin_mean = []
    bin_std = []

    for jj, idx in enumerate(idxs):
        jj += 1
        if idx:
            bin_mean.append(ydata[digitized == jj].mean())
            bin_std.append(ydata[digitized == jj].std())
        else:
            bin_mean.append(np.nan)
            bin_std.append(np.nan)

    return xc, bin_count, np.array(bin_mean), np.array(bin_std)
