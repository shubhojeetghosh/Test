/* =========================================
   CONFIG
   ========================================= */

const SET_PRICE = 50;

// WhatsApp number with country code.
// India: 91 + mobile number
// No +, spaces, or hyphens.

const WHATSAPP_BUSINESS_NUMBER = "919547428567";
const STUDENT_ACCESS_REQUEST_URL =
  `${(window.EPS_API?.baseUrl || window.API_BASE_URL || "").replace(/\/+$/, "")}/api/student/access-requests`;

function escapePaymentHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


/* =========================================
   ELEMENTS
   ========================================= */

const selectedSetsContainer =
  document.getElementById("selectedSetsContainer");

const summarySetCount =
  document.getElementById("summarySetCount");

const summaryTotal =
  document.getElementById("summaryTotal");

const whatsappButton =
  document.getElementById("whatsappButton");


/* =========================================
   CATEGORY NAMES
   ========================================= */

const categoryNames = {

  vowels: "Korean Vowels & Consonants",

  numbers: "Korean Numbers",

  counting: "Counting Units",

  speech: "Parts of Speech",

  tense: "Tense",

  formal: "Formal & Informal Language",

  indirect: "Indirect Speech",

  textbook: "EPS TOPIK TEXT BOOK"

};


/* =========================================
   LOAD CART
   ========================================= */

function loadCart() {

  const storedCart =
    sessionStorage.getItem("epsTopikCart");

  if (!storedCart) {

    showEmptyCart();

    return [];

  }

  try {

    const cart =
      JSON.parse(storedCart);

    if (
      !cart.items ||
      !Array.isArray(cart.items) ||
      cart.items.length === 0
    ) {

      showEmptyCart();

      return [];

    }

    return cart.items;

  }

  catch (error) {

    console.error(
      "Invalid cart data:",
      error
    );

    showEmptyCart();

    return [];

  }

}


/* =========================================
   EMPTY CART
   ========================================= */

function showEmptyCart() {

  selectedSetsContainer.innerHTML = `

    <div class="empty-cart">

      No paid test sets selected.

      <br><br>

      <a href="set.html">
        ← Choose Test Sets
      </a>

    </div>

  `;

  summarySetCount.textContent = "0";

  summaryTotal.textContent = "NPR 0";

  whatsappButton.disabled = true;

  whatsappButton.style.opacity = "0.5";

  whatsappButton.style.cursor = "not-allowed";

}


/* =========================================
   RENDER ORDER
   ========================================= */

function renderCart(items) {

  selectedSetsContainer.innerHTML = "";

  items.forEach(item => {

    const categoryName =
      categoryNames[item.category] ||
      item.categoryName ||
      item.category;

    const formattedSet =
      String(item.set).padStart(2, "0");

    const setElement =
      document.createElement("div");

    setElement.className =
      "selected-set-item";

    setElement.innerHTML = `

      <div class="selected-set-info">

        <strong>
          ${escapePaymentHtml(categoryName)}
        </strong>

        <span>
          Set No. ${formattedSet}
        </span>

      </div>

      <div class="selected-set-price">
        NPR ${SET_PRICE}
      </div>

    `;

    selectedSetsContainer.appendChild(
      setElement
    );

  });


  const total =
    items.length * SET_PRICE;

  summarySetCount.textContent =
    items.length;

  summaryTotal.textContent =
    `NPR ${total}`;

}


/* =========================================
   BUILD WHATSAPP MESSAGE
   ========================================= */

function buildWhatsAppMessage(items) {

  const total =
    items.length * SET_PRICE;

  let message =
`Hello EPS TOPIK Team,

I would like to purchase the following test sets:

`;

  items.forEach(
    (item, index) => {

      const categoryName =
        categoryNames[item.category] ||
        item.categoryName ||
        item.category;

      const formattedSet =
        String(item.set).padStart(2, "0");

      message +=
`${index + 1}. ${categoryName} - Set No. ${formattedSet} - NPR ${SET_PRICE}
`;

    }
  );


  message +=
`
Total Sets: ${items.length}
Total Amount: NPR ${total}

Please send me the official payment instructions for these exam sets. I understand that this chat is with the Quiz Platform administrator to arrange my purchase. I will not send passwords, one-time codes (OTPs), card PINs, or full card details in chat.

Thank you.`;

  return message;

}


/* =========================================
   OPEN WHATSAPP CHAT
   ========================================= */

function openWhatsApp(items) {

  if (items.length === 0) {
    return;
  }

  const message =
    buildWhatsAppMessage(items);

  const encodedMessage =
    encodeURIComponent(message);

  const whatsappURL =
    `https://wa.me/${WHATSAPP_BUSINESS_NUMBER}?text=${encodedMessage}`;

  window.location.href =
    whatsappURL;

}


/* =========================================
   INITIAL LOAD
   ========================================= */

const cartItems =
  loadCart();


if (cartItems.length > 0) {

  renderCart(cartItems);

  whatsappButton.addEventListener(
    "click",
    async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        window.location.href = "login.html?next=" + encodeURIComponent("payment.html?mode=cart");
        return;
      }
      if (!STUDENT_ACCESS_REQUEST_URL.startsWith("http")) {
        alert("The payment request service is not configured. Please contact the administrator.");
        return;
      }

      whatsappButton.disabled = true;
      const originalLabel = whatsappButton.textContent;
      whatsappButton.textContent = "Sending set request…";
      try {
        const response = await fetch(STUDENT_ACCESS_REQUEST_URL, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            exam_set_ids: cartItems.map(item => Number(item.set))
          })
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.detail || "Could not send your selected sets to the administrator.");
        }
        openWhatsApp(cartItems);
      } catch (error) {
        console.error("Could not create set purchase request:", error);
        alert(error.message || "Could not send your set request. Please try again.");
        whatsappButton.disabled = false;
        whatsappButton.textContent = originalLabel;
      }
    }
  );

}
