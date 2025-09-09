(function () {
  var hideDebugButtonForLabelPopup = true;
  var $ = Veams.$;

  function init() {
    if($("body.preview").length > 0 && !hideDebugButtonForLabelPopup){
      createButton();
    }
  }

  function renderValues() {
    prepareHtml();
    var values = Object.values(getValues());
    var label = values.filter(function (item) { return item.type=="label"});
    var settings = values.filter(function (item) { return item.type=="setting"});
    populateTable(".js-label-values[data-type='label']",label);
    populateTable(".js-label-values[data-type='settings']",settings);
  }

  function populateTable(table,values) {
    $(table).append("<tr><th>Key</th><th>Wert</th><th>Template</th></tr>")
    values.forEach(function (item) {
      var tr = $("<tr/>");
      tr.append($("<td/>",{"html":item.key}));
      tr.append($("<td/>",{"html":item.value}));
      tr.append($("<td/>",{"html":item.template[0],"data-template":item.template}));
      $(table).append(tr);
    });
  }

  function showTab() {
    if(!$(this).is("active")){
      $(this).siblings().removeClass("active");
      $(this).addClass("active");
      var index = $(this).index();
      $(".js-label-content .js-label-values").hide();
      var show = $(".js-label-content .js-label-values")[index];
      $(show).show();
    }
  }

  function getValues() {
    var values = {};
    $(".js-label-config").each(function (index, item) {
      var key = $(item).data("key");
      if (typeof values[key] == "undefined") {
        var value = $.extend({},$(item).data());
        value.template = [];
        values[key] = value;
      }
      values[key].template.push($(item).data("template"));
    });
    return values;
  }
  function prepareHtml() {
    close();
    $("main").prepend($("<div/>", {"class": "js-label-container"}));
    $(".js-label-container").append($("<div/>", {"class": "js-label-header"}));
    $(".js-label-header").append("<div class='js-label-header-button active'>Label</div>");
    $(".js-label-header").append("<div class='js-label-header-button'>Settings</div>");
    $(".js-label-header").append("<div class='js-label-close'></div>");
    $(".js-label-container").append($("<div/>", {"class": "js-label-content"}));
    $(".js-label-content").append($("<table/>", {"class": "js-label-values","data-type":"label"}));
    $(".js-label-content").append($("<table/>", {"class": "js-label-values","data-type":"settings"}));
    $(".js-label-content .js-label-values[data-type='settings']").hide();
    $(".js-label-header-button").on("click", showTab);
    $(".js-label-close").on("click", close);
  }

  function close() {
    $(".js-label-container").remove();
  }
  function createButton() {
    var button = $("<li/>", {"class": "metanavigation__linklist-item"});
    var a = $("<a/>", {"class": "metanavigation__link", "href": "javascript:void(0)"});
    var span = $("<span/>", {"class": "metanavigation__link-content", "html": "Debug button"});
    a.append(span);
    a.on("click", renderValues);
    button.append(a);
    $(".metanavigation__linklist").append(button);
  }

  init();
})();
