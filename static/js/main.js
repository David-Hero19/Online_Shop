// ── Nexus Store — main.js ──

function showToast(msg, type = "success") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast show" + (type === "error" ? " error" : "");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.className = "toast"; }, 3000);
}

function updateBadge(count) {
  const badge = document.getElementById("cartBadge");
  if (!badge) return;
  badge.textContent = count;
  badge.style.display = count > 0 ? "inline-flex" : "none";
}

async function addToCart(productId, btn) {
  const orig = btn.textContent;
  btn.textContent = "Adding…";
  btn.disabled = true;
  try {
    const res = await fetch("/api/cart/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, quantity: 1 })
    });
    const data = await res.json();
    if (data.success) {
      updateBadge(data.cart_count);
      btn.textContent = "Added!";
      btn.classList.add("added");
      showToast("Item added to cart ✓");
      setTimeout(() => {
        btn.textContent = orig;
        btn.classList.remove("added");
        btn.disabled = false;
      }, 1200);
    }
  } catch (e) {
    showToast("Failed to add item", "error");
    btn.textContent = orig;
    btn.disabled = false;
  }
}
