function start_download_model(button, idx){
    button.disabled = "disabled"
    button.value = "Downloading..."

    let textarea = gradioApp().querySelector(`#download_idx_number input`)
    textarea.value = idx
    textarea.dispatchEvent(new Event("input", { bubbles: true }))

    gradioApp().querySelector(`#download_model_button`).click()
}
