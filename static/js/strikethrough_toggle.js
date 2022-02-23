
function manageStrikethrough(button){
    hidden = document.getElementById(button.id.replace("button", "hidden"))
    let initial_strikethrough = button.style.getPropertyValue("text-decoration") == "line-through";
    let strikethrough = !initial_strikethrough
    if(!strikethrough) {
        button.classList.remove("btn-secondary");
        button.classList.add("btn-primary");
        button.classList.remove("item-remove");
        hidden.value = "keep";

        button.style.setProperty("text-decoration", "");
    } else {
        button.classList.add("btn-secondary");
        button.classList.remove("btn-primary");
        button.classList.add("item-remove");
        button.style.setProperty("text-decoration", "line-through");
        hidden.value = "delete";
    }
    return strikethrough;
}