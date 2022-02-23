//var Migrations = artifacts.require("Migrations");

var Trading = artifacts.require("./Trading.sol");
var Processing = artifacts.require("./Processing.sol");
module.exports = function(deployer) {
  deployer.deploy(Trading);
  deployer.deploy(Processing);
};


