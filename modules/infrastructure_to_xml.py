# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 16:05:20 2025

@author: Francesco Brandoli
"""
import xml.etree.ElementTree as ET
import os

def infrastructure_to_xml(infrastructure, output_path):
    """
    Given an Infrastructure object (from parsing_xml.py),
    writes its nodeList to an XML file in the same format as xml_generator.py.
    """
    root = ET.Element("infrastructure")

    for node in infrastructure.nodeList:
        node_elem = ET.SubElement(root, "node")

        ET.SubElement(node_elem, "id").text = f"{node.type}:{node.id}"
        ET.SubElement(node_elem, "type").text = node.type
        if node.Ncore != 0:
            ET.SubElement(node_elem, "Ncore").text = str(node.Ncore)
        else:
            ET.SubElement(node_elem, "Ncore").text = str(node.Ncore+1e-10)
        if node.mainMemory !=0 :
            ET.SubElement(node_elem, "mainMemory").text = str(node.mainMemory)
        else:
            ET.SubElement(node_elem, "mainMemory").text = str(node.mainMemory+1e-10)            
        ET.SubElement(node_elem, "power").text = str(node.power)
        ET.SubElement(node_elem, "risk").text = str(node.risk)
        ET.SubElement(node_elem, "region").text = str(node.region)
        ET.SubElement(node_elem, "eprice").text = str(node.eprice)
        ET.SubElement(node_elem, "activation").text = str(int(node.activation))

    # Write out the XML
    tree = ET.ElementTree(root)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    print(f"Infrastructure XML successfully written to: {output_path}")
