/* =========================================
   CONFIG
   ========================================= */

const SET_PRICE = 50;

// WhatsApp number with country code.
// India: 91 + mobile number
// No +, spaces, or hyphens.

const WHATSAPP_BUSINESS_NUMBER = "919547428567";


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
          ${categoryName}
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

Please provide the payment details and help me activate these test sets after payment.

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
    () => {

      openWhatsApp(cartItems);

    }
  );

}