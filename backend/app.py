from flask import Flask, render_template, request
from waitress import serve
import sqlite3
import math
import os

app = Flask(__name__, template_folder="../frontend")

DATABASE = "backend/database.db"


# -----------------------------
# conexão banco
# -----------------------------
def get_db():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


# -----------------------------
# criar tabela
# -----------------------------
def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS calculos (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        tensao REAL,
        altura REAL,
        largura REAL,
        potencia_desejada REAL,
        rs REAL,

        AT REAL,
        AB REAL,
        BL REAL,
        BR REAL,
        LB REAL,

        espacos INTEGER,
        cortes INTEGER,
        passo REAL,

        resistencia REAL,
        potencia REAL

    )

    """)

    conn.commit()
    conn.close()


# -----------------------------
# cálculo resistivo
# -----------------------------
def calcular_resistivo(V, H, W, P_alvo, Rs, AT, AB, BL, BR, LB):

    R_alvo = (V**2) / P_alvo

    # altura ativa
    H_ativo = H - (AT + AB + 2 * LB)

    # largura ativa
    W_ativo = W

    N_teorico = math.sqrt((R_alvo * W_ativo) / (Rs * H_ativo))

    candidatos = []

    for N in range(max(1, int(N_teorico) - 3), int(N_teorico) + 4):

        passo = W_ativo / N

        comprimento = N * H_ativo

        squares = comprimento / passo

        cortes = N - 1

        fator = 1 + (0.0022 * cortes)

        resistencia = Rs * squares * fator

        potencia = (V**2) / resistencia

        erro = abs(potencia - P_alvo)

        candidatos.append({

            "espacos": N,
            "cortes": cortes,
            "passo": round(passo, 2),
            "resistencia": round(resistencia),
            "potencia": round(potencia),
            "erro": erro

        })

    melhor = min(candidatos, key=lambda x: x["erro"])

    return melhor


# -----------------------------
# salvar cálculo
# -----------------------------
def salvar_calculo(V, H, W, P, Rs, AT, AB, BL, BR, LB, resultado):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO calculos (

        tensao,
        altura,
        largura,
        potencia_desejada,
        rs,

        AT, AB, BL, BR, LB,

        espacos,
        cortes,
        passo,
        resistencia,
        potencia

    )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        V, H, W, P, Rs,
        AT, AB, BL, BR, LB,

        resultado["espacos"],
        resultado["cortes"],
        resultado["passo"],
        resultado["resistencia"],
        resultado["potencia"]

    ))

    conn.commit()
    conn.close()


# -----------------------------
# rota principal
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():

    resultado = None

    if request.method == "POST":

        V = float(request.form["tensao"])
        H = float(request.form["altura"])
        W = float(request.form["largura"])
        P = float(request.form["potencia"])
        Rs = float(request.form["rs"])

        AT = float(request.form["AT"])
        AB = float(request.form["AB"])
        BL = float(request.form["BL"])
        BR = float(request.form["BR"])
        LB = float(request.form["LB"])

        resultado = calcular_resistivo(V, H, W, P, Rs, AT, AB, BL, BR, LB)

        salvar_calculo(V, H, W, P, Rs, AT, AB, BL, BR, LB, resultado)

    return render_template("Calculo_Resistivo.html", resultado=resultado)


# -----------------------------
# inicialização
# -----------------------------
init_db()


# -----------------------------
# servidor
# -----------------------------
if __name__ == "__main__":

    print("Servidor iniciado com Waitress...")

    port = int(os.environ.get("PORT", 5000))

    serve(
        app,
        host="0.0.0.0",
        port=port
    )