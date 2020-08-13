function getAllCheckboxes() {
  return Array.from(document.getElementsByTagName("input")).filter(
    (elem) => elem.type === "checkbox"
  );
}

function checkAll(allbox) {
  /* Mark or unmark all checkboxes */
  getAllCheckboxes().forEach((box) => {
    box.checked = allbox.checked;
  });
}

function checkCSRankings(csbox) {
  /* Mark or unmark all csrankings checkboxes */
  getAllCheckboxes().forEach((box) => {
    if (box.id.includes("*")) {
      box.checked = csbox.checked;
    }
  });
  allChecked();
}

function checkParts(partbox) {
  /* Mark or unmark all sub boxes under the given "partbox" */
  Array.from(document.getElementsByName(partbox.id)).forEach((box) => {
    box.checked = partbox.checked;
  });
  allChecked();
}

function allChecked() {
  /* Check if upper checkboxes(ex. all, csrankings, each of partboxes) are
     marked properly. If not, mark or unmark them correctly. */

  field_table.forEach((row) => {
    row.forEach((field) => {
      let field_name = field[0];
      let partbox = document.getElementById(field_name);

      partbox.checked = true;
      Array.from(document.getElementsByName(field_name)).forEach((box) => {
        if (!box.checked) {
          partbox.checked = false;
        }
      });
    });
  });

  const allbox = document.getElementById("all");
  const csbox = document.getElementById("CSRankings");
  const boxes = getAllCheckboxes();

  csbox.checked = true;
  boxes.forEach((box) => {
    if (box.id.includes("*") && !box.checked) {
      csbox.checked = false;
    }
  });

  var checked_cnt = 0;
  boxes.forEach((box) => {
    if (!box.checked) {
      checked_cnt++;
    }
  });
  allbox.checked = checked_cnt < 2 ? true : false;
}

function submit() {
  const query_array = getAllCheckboxes()
    // !!box.name is true <=> box is conference
    .filter((box) => !!box.name && box.checked)
    .map((box) => "conferences=" + box.id.replace("*", "").replace(" ", "%20"))
    .concat(
      [
        "from_year",
        "to_year",
        "author_filter",
        "author_limit",
        "min_num_pages",
      ].map((label) => label + "=" + document.getElementById(label).value)
    );

  const women_filter = document.getElementById("women_filter");
  if (!!women_filter) {
    query_array.push("women_filter=" + women_filter.value);
  }

  if (window.location === "/") {
    window.location = "/results?" + query_array.join("&");
  } else {
    window.location = window.location + "results?" + query_array.join("&");
  }
}
