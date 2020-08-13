let vis = d3.select("svg");
let w = vis.style("width").replace("px", "");
let h = vis.style("height").replace("px", "");

let nodes = [];
let links = [];
let labelAnchors = [];
let labelAnchorLinks = [];
let label_dict = {};

for (let i = 0; i < result.length; i++) {
  let author_name = result[i][0];
  let node = { label: author_name };
  nodes.push(node);
  labelAnchors.push({ node: node });
  labelAnchors.push({ node: node });
  label_dict[author_name] = i;
}

for (let author in weight_dict) {
  for (let coauthor in weight_dict[author]) {
    links.push({
      source: label_dict[author],
      target: label_dict[coauthor],
      weight: weight_dict[author][coauthor],
    });
  }
}

for (let i = 0; i < nodes.length; i++) {
  labelAnchorLinks.push({
    source: i * 2,
    target: i * 2 + 1,
    weight: 1,
  });
}

function getNodeSize(node) {
  return Math.max(
    5,
    20 *
      Math.sqrt(result[label_dict[node.label]][2].length / max_num_publications)
  );
}

let force = d3.layout
  .force()
  .size([w, h])
  .nodes(nodes)
  .links(links)
  .gravity(2)
  .linkDistance(50)
  .charge(-3000)
  .linkStrength(0.5);
force.start();

let force2 = d3.layout
  .force()
  .nodes(labelAnchors)
  .links(labelAnchorLinks)
  .gravity(0)
  .linkDistance(0)
  .linkStrength(4)
  .charge(-100)
  .size([w, h]);
force2.start();

let link = vis
  .selectAll("line.link")
  .data(links)
  .enter()
  .append("svg:line")
  .attr("class", "link")
  .style("stroke", "#CCC");

let node = vis
  .selectAll("g.node")
  .data(force.nodes())
  .enter()
  .append("svg:g")
  .attr("class", "node");

node
  .append("svg:circle")
  .attr("r", getNodeSize)
  .style("fill", "rgba(169,183,192,1)")
  .style("stroke", "#FFF")
  .style("stroke-width", 2);
node.call(force.drag);

let anchorLink = vis.selectAll("line.anchorLink").data(labelAnchorLinks);
//.enter().append("svg:line").attr("class", "anchorLink").style("stroke", "#999");

let anchorNode = vis
  .selectAll("g.anchorNode")
  .data(force2.nodes())
  .enter()
  .append("svg:g")
  .attr("class", "anchorNode");

anchorNode.append("svg:circle").attr("r", 0).style("fill", "#FFF");
anchorNode
  .append("svg:text")
  .text(function (d, i) {
    return i % 2 == 0 ? "" : d.node.label;
  })
  .style("fill", "#555")
  .style("font-family", "Arial")
  .style("font-size", 12);

let updateLink = function () {
  this.attr("x1", function (d) {
    return d.source.x;
  })
    .attr("y1", function (d) {
      return d.source.y;
    })
    .attr("x2", function (d) {
      return d.target.x;
    })
    .attr("y2", function (d) {
      return d.target.y;
    });
};

let updateNode = function () {
  this.attr("transform", function (d) {
    return "translate(" + d.x + "," + d.y + ")";
  });
};

force.on("tick", function () {
  force2.start();

  node.call(updateNode);

  anchorNode.each(function (d, i) {
    if (i % 2 == 0) {
      d.x = d.node.x;
      d.y = d.node.y;
    } else {
      let b = this.childNodes[1].getBBox();

      let diffX = d.x - d.node.x;
      let diffY = d.y - d.node.y;

      let dist = Math.sqrt(diffX * diffX + diffY * diffY);

      let shiftX = (b.width * (diffX - dist)) / (dist * 2);
      shiftX = Math.max(-b.width, Math.min(0, shiftX));
      let shiftY = 5;
      this.childNodes[1].setAttribute(
        "transform",
        "translate(" + shiftX + "," + shiftY + ")"
      );
    }
  });

  anchorNode.call(updateNode);

  link.call(updateLink);
  anchorLink.call(updateLink);
});
