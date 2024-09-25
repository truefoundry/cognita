const FormatMapper = {
  "PDF": "application/pdf",
  "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "PPTX": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  "TXT": "text/plain",
  "CSV": "text/csv",
  "JSON": "application/json",
  "XML": "application/xml",
  "HTML": "text/html",
}


export async function getFileFromS3(fileName: string, url: string, fileFormat: string): Promise<File | null> {
  const response = await fetch(url);
  const fileContent = await response.blob()

  if (FormatMapper[fileFormat as keyof typeof FormatMapper] === undefined) {
    return null;
  }

  return new File([fileContent], fileName, {
    type: FormatMapper[fileFormat as keyof typeof FormatMapper]
  });
}
