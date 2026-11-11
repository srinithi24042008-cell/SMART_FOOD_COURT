const Cart = {
    KEY: 'campus_food_court_cart',

    getItems() {
        try {
            return JSON.parse(localStorage.getItem(this.KEY)) || [];
        } catch (e) {
            return [];
        }
    },

    saveItems(items) {
        localStorage.setItem(this.KEY, JSON.stringify(items));
        this.updateBadge();
        window.dispatchEvent(new CustomEvent('cartUpdated', { detail: items }));
    },

    addItem(food) {
        let items = this.getItems();
        let existing = items.find(i => i.id === food.id);
        if (existing) {
            if (existing.quantity >= food.stock_quantity) {
                this.showToast(`Only ${food.stock_quantity} available in stock!`, 'warning');
                return false;
            }
            existing.quantity += 1;
        } else {
            if (food.stock_quantity < 1) {
                this.showToast(`Item is currently out of stock.`, 'danger');
                return false;
            }
            items.push({
                id: food.id,
                name: food.name,
                price: food.price,
                image_url: food.image_url,
                is_veg: food.is_veg,
                stock_quantity: food.stock_quantity,
                prep_time_mins: food.prep_time_mins,
                quantity: 1
            });
        }
        this.saveItems(items);
        this.showToast(`Added ${food.name} to cart!`, 'success');
        return true;
    },

    updateQuantity(foodId, delta) {
        let items = this.getItems();
        let idx = items.findIndex(i => i.id === foodId);
        if (idx !== -1) {
            let newQty = items[idx].quantity + delta;
            if (newQty <= 0) {
                items.splice(idx, 1);
            } else if (newQty > items[idx].stock_quantity) {
                this.showToast(`Cannot exceed remaining stock (${items[idx].stock_quantity})`, 'warning');
                return;
            } else {
                items[idx].quantity = newQty;
            }
            this.saveItems(items);
        }
    },

    removeItem(foodId) {
        let items = this.getItems().filter(i => i.id !== foodId);
        this.saveItems(items);
    },

    clear() {
        localStorage.removeItem(this.KEY);
        this.updateBadge();
        window.dispatchEvent(new CustomEvent('cartUpdated', { detail: [] }));
    },

    getCount() {
        return this.getItems().reduce((acc, itm) => acc + itm.quantity, 0);
    },

    getTotal() {
        return this.getItems().reduce((acc, itm) => acc + (itm.price * itm.quantity), 0);
    },

    updateBadge() {
        const count = this.getCount();
        document.querySelectorAll('.cart-count-badge').forEach(el => {
            el.textContent = count;
            el.style.display = count > 0 ? 'inline-block' : 'none';
        });
        const totalEls = document.querySelectorAll('.cart-total-badge');
        totalEls.forEach(el => {
            el.textContent = `₹${this.getTotal().toFixed(2)}`;
        });
    },

    showToast(message, type = 'info') {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const bgMap = {
            success: 'bg-success text-white',
            warning: 'bg-warning text-dark',
            danger: 'bg-danger text-white',
            info: 'bg-primary text-white'
        };

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center ${bgMap[type] || 'bg-dark text-white'} border-0 show shadow-lg mb-2`;
        toastEl.setAttribute('role', 'alert');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body fw-medium">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        container.appendChild(toastEl);
        setTimeout(() => {
            toastEl.classList.remove('show');
            setTimeout(() => toastEl.remove(), 300);
        }, 3200);
    }
};

const Notifs = {
    async fetch() {
        try {
            const res = await fetch('/api/notifications');
            if (!res.ok) return;
            const data = await res.json();
            if (data.success) {
                this.render(data.notifications, data.unread_count);
            }
        } catch (e) {
            console.error('Error fetching notifications:', e);
        }
    },

    render(list, unreadCount) {
        const badge = document.getElementById('notifBadge');
        if (badge) {
            badge.textContent = unreadCount;
            badge.style.display = unreadCount > 0 ? 'flex' : 'none';
        }
        const container = document.getElementById('notifList');
        if (container) {
            if (!list || list.length === 0) {
                container.innerHTML = `<div class="p-3 text-center text-muted small"><i class="bi bi-bell-slash fs-4 d-block mb-1"></i>No notifications yet</div>`;
                return;
            }
            container.innerHTML = list.map(n => `
                <div class="notif-item ${n.is_read ? '' : 'unread'}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="fw-bold small text-dark">${n.title}</div>
                        <span class="text-muted" style="font-size: 0.7rem;">${n.created_at ? n.created_at.split(' ')[1] : ''}</span>
                    </div>
                    <div class="text-secondary small mt-1">${n.message}</div>
                </div>
            `).join('');
        }
    },

    async markAllRead() {
        try {
            await fetch('/api/notifications/mark-read', { method: 'POST' });
            this.fetch();
        } catch (e) {
            console.error(e);
        }
    },

    startPolling(intervalMs = 6000) {
        this.fetch();
        setInterval(() => this.fetch(), intervalMs);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Cart.updateBadge();
    Notifs.startPolling();

    const notifBtn = document.getElementById('notifDropdownBtn');
    if (notifBtn) {
        notifBtn.addEventListener('click', () => {
            Notifs.markAllRead();
        });
    }
});
