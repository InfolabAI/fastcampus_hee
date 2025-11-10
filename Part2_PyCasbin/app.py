from flask import Flask, request, jsonify
import casbin

app = Flask(__name__)

# Casbin Enforcer 초기화
e = casbin.Enforcer("model.conf", "policy.csv")

@app.route("/data1", methods=["GET", "POST"])
def handle_data():
    user = request.args.get("user")  # ?user=alice
    act = "read" if request.method == "GET" else "write"
    obj = "data1"

    if e.enforce(user, obj, act):
        return jsonify({"message": f"{user} allowed to {act} {obj}"}), 200
    else:
        return jsonify({"error": f"{user} NOT allowed to {act} {obj}"}), 403

if __name__ == "__main__":
    app.run(debug=True)
