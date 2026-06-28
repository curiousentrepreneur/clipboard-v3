# Labs Clipboard v0.5 Pairing Debug

Bu sürümde normal PIN eşleştirmesi duruyor ama ayrıca **Acil test eşleştir (PIN yok)** butonu eklendi.

Kullanım:
1. İki bilgisayarda da bu v0.5 paketini çalıştır.
2. Karşı bilgisayarda uygulama açık olsun.
3. Bu bilgisayarda + Cihaz ekle > Bağlan sekmesine gir.
4. IP alanına karşı bilgisayarın 192.168.x.x IP adresini yaz.
5. **Acil test eşleştir (PIN yok)** butonuna bas.

Bu çalışırsa ağ/port çalışıyor, sorun PIN akışında demektir.
Bu da çalışmazsa sorun Windows Güvenlik Duvarı, yanlış IP veya iki cihazın farklı ağda olmasıdır.

Not: Acil test eşleştirme üretim güvenliği için kalıcı özellik değildir.
