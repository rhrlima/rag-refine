from flask import Flask, render_template, request
from calculator import (
    simulate,
    EquipType,
    DEFAULTS
)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        initial_over = int(request.form['initial_over'])
        target_over = int(request.form['target_over'])
        equip_type = EquipType.WEAPON if request.form['equip_type'] == 'weapon' else EquipType.ARMOR

        kwargs = {}
        for i in range(4, 10):
            kwargs[f'over_{i}'] = True if f'over_{i}' in request.form else False

        DEFAULTS['bsb_price'] = int(request.form['bsb_price'])
        
        result = simulate(
            initial_over,
            target_over,
            equip_type,
            **kwargs
        )
        return render_template('form.html', defaults=DEFAULTS, result=result)

    return render_template('form.html', defaults=DEFAULTS)

if __name__ == '__main__':
    app.run(debug=True)
