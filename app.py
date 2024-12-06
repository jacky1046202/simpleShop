from flask import Flask, render_template, redirect, url_for, request, flash, session
from config import Config
from models import db, Item

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()  # 初始化資料庫

# 主頁面 - 顯示商品清單
@app.route('/')
def index():
    items = Item.query.all()
    return render_template('index.html', items=items)

# 新增商品頁面
@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        quantity = request.form.get('quantity')
        if name and price and quantity:
            try:
                price = float(price)
                quantity = int(quantity)
                item = Item(name=name, price=price, quantity=quantity)
                db.session.add(item)
                db.session.commit()
                flash("商品新增成功！", "success")
                return redirect(url_for('index'))
            except ValueError:
                flash("價格和數量必須是數字！", "danger")
        else:
            flash("請填寫所有欄位！", "danger")
    return render_template('add_item.html')

# 刪除商品
@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("商品已刪除！", "info")
    return redirect(url_for('index'))

# 編輯商品信息
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.price = float(request.form.get('price'))
        item.quantity = int(request.form.get('quantity'))
        db.session.commit()
        flash("商品信息已更新！", "success")
        return redirect(url_for('index'))
    return render_template('edit_item.html', item=item)

# 商品詳情頁面
@app.route('/detail/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item_detail.html', item=item)

# 添加到購物車
@app.route('/add_to_cart/<int:item_id>', methods=['GET', 'POST'])
def add_to_cart(item_id):
    item = Item.query.get_or_404(item_id)
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']
    if request.method == 'POST':
        quantity = request.form.get('quantity')
        try:
            quantity = int(quantity)
            if quantity > 0:
                if item.quantity >= quantity:
                    if str(item.id) in cart:
                        cart[str(item.id)]['quantity'] += quantity
                    else:
                        cart[str(item.id)] = {'name': item.name, 'price': item.price, 'quantity': quantity}
                    session['cart'] = cart
                    flash(f"成功加入 {quantity} 個 {item.name} 到購物車", "success")
                else:
                    flash("庫存不足！", "danger")
            else:
                flash("購買數量必須大於0！", "danger")
        except ValueError:
            flash("購買數量必須是整數！", "danger")
    else:
        if str(item.id) in cart:
            flash(f"{item.name} 已在購物車中，不可重複加入！", "warning")
        else:
            cart[str(item.id)] = {'name': item.name, 'price': item.price, 'quantity': 1}
            session['cart'] = cart
            flash(f"成功加入 1 個 {item.name} 到購物車", "success")
    return redirect(url_for('index'))

# 購物車頁面
@app.route('/cart')
def cart():
    return render_template('cart.html')

# 移除購物車商品
@app.route('/remove_from_cart/<string:item_id>')
def remove_from_cart(item_id):
    if 'cart' in session:
        if item_id in session['cart']:
            del session['cart'][item_id]
            session.modified = True
            flash("商品已從購物車中移除！", "info")
    return redirect(url_for('cart'))

# 結帳
@app.route('/checkout')
def checkout():
    if 'cart' in session and len(session['cart']) > 0:
        cart = session['cart']
        for item_id, item_info in cart.items():
            item = Item.query.get(item_id)
            if item:
                item.quantity -= item_info['quantity']
                db.session.commit()
        session.pop('cart', None)
        flash("結帳成功，感謝您的購買！", "success")
        return render_template('checkout.html')
    else:
        flash("購物車是空的，無法結帳！", "warning")
        return redirect(url_for('cart'))

# 搜索功能
@app.route('/search')
def search():
    query = request.args.get('query', '')
    if query:
        items = Item.query.filter(Item.name.contains(query)).all()
    else:
        items = []
    return render_template('search_results.html', items=items, query=query)

@app.context_processor
def inject_total_price():
    def total_price():
        total = 0
        if 'cart' in session:
            for item_id, item_info in session['cart'].items():
                total += item_info['price'] * item_info['quantity']
        return total
    return {'total_price': total_price}

if __name__ == '__main__':
    app.run(debug=True)