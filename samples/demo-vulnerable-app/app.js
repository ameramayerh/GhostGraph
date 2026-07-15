const apiKey = "demo-secret-value-only-for-scanner";

function showPreview(userSuppliedHtml) {
  document.getElementById("preview").innerHTML = userSuppliedHtml;
}

function calculate(expression) {
  return eval(expression);
}

module.exports = { apiKey, showPreview, calculate };
