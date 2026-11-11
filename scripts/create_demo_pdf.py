from pathlib import Path

import pymupdf


def main():
    output_path = Path("data/raw/RFI_040.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pymupdf.open() as pdf:
        page1 = pdf.new_page()
        page1.insert_text((72, 72), "REQUEST FOR INFORMATION\nRFI Number: RFI-040\nProject: Demo Boston Office Tower\nSubject: Electrical Conduit Conflict\nStatus: Open", fontsize=12)

        page2 = pdf.new_page()
        page2.insert_text((72, 72), "Question:\nElectrical conduits conflict with HVAC ductwork on Level 4.\nPlease provide revised coordination drawings.\nResponsible Party: MEP Engineer", fontsize=12)

        pdf.save(str(output_path))

    print(f"Created PDF: {output_path}")


if __name__ == "__main__":
    main()
