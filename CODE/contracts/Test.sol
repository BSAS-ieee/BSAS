pragma solidity ^0.5.12;


contract Trading {
    
    struct Car{
        address car_addr;
        uint[16] map;

    }
    
    function StringToBytesVer1(string memory source) internal pure returns (bytes memory) {
        return bytes(source);
    }
    function bytesToAddress(bytes memory bys) internal pure returns (address addr) {
      assembly {
        addr := mload(add(bys,20))
      }
    }
  
    uint car_num;
    mapping (uint=>Car) car_map;

    function ReceiveCD (string memory _caraddress_s,uint[16] memory _map) public returns(uint[16] memory) {
        bytes memory add_byte=StringToBytesVer1(_caraddress_s);
        address _caraddress=bytesToAddress(add_byte);
        car_num++;
        car_map[car_num] = Car(_caraddress,_map);
        return (car_map[car_num].map);
    } 
    
    function storageToMemory(uint o) pure internal returns(uint){
        return o;
    }
    function R_car_num() public view returns(uint){
        return storageToMemory(car_num);
    }
    
    function SendTX(uint _car_num) public view returns(uint[16] memory){
        Car storage c = car_map[_car_num];
        return (c.map);
    }

    function Resp_s(Processing processing) public view returns(uint){
        return processing.SeSpeed();
    }
}

contract Processing {
    uint speed;
    
    function ReSpeed(uint sp) public returns(uint){
        speed=sp;
        uint sp_m=speed;
        return sp_m;
    }

    function SeSpeed() public view returns(uint){
       uint RecommandSpeed = speed;
       return RecommandSpeed;
    }
}




